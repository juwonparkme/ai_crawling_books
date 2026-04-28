from __future__ import annotations

import json
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path

from .service import RunSettings, load_run_file, run_crawler, validate_settings


def main() -> int:
    try:
        from PyQt6.QtCore import Qt, QTimer
        from PyQt6.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QFileDialog,
            QFormLayout,
            QGridLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QSpinBox,
            QSplitter,
            QTableWidget,
            QTableWidgetItem,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except ModuleNotFoundError as exc:
        print("PyQt6 is required. Install with: python3 -m pip install -r requirements.txt", file=sys.stderr)
        raise SystemExit(2) from exc

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("ai_crawling_books")
            self.resize(1180, 760)
            self.events: queue.Queue[tuple[str, str]] = queue.Queue()
            self.cancel_event = threading.Event()
            self.worker: threading.Thread | None = None
            self.current_payload: dict | None = None
            self.log_path: Path | None = None

            root = QWidget()
            self.setCentralWidget(root)
            outer = QHBoxLayout(root)
            outer.setContentsMargins(14, 14, 14, 14)

            form_panel = QWidget()
            form_panel.setMaximumWidth(360)
            form = QFormLayout(form_panel)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

            self.title_input = QLineEdit()
            self.title_input.setPlaceholderText("Database System Concepts")
            self.author_input = QLineEdit()
            self.author_input.setPlaceholderText("Silberschatz")
            self.out_input = QLineEdit(str(Path.cwd() / "result"))
            self.browse_button = QPushButton("Browse")
            out_row = QHBoxLayout()
            out_row.addWidget(self.out_input)
            out_row.addWidget(self.browse_button)
            out_widget = QWidget()
            out_widget.setLayout(out_row)

            self.provider_input = QComboBox()
            self.provider_input.addItems(["brave", "bing"])
            self.english_input = QCheckBox("English")
            self.korean_input = QCheckBox("Korean")
            self.english_input.setChecked(True)
            self.korean_input.setChecked(True)
            self.max_results_input = QSpinBox()
            self.max_results_input.setRange(1, 100)
            self.max_results_input.setValue(20)
            self.retries_input = QSpinBox()
            self.retries_input.setRange(0, 10)
            self.retries_input.setValue(2)
            self.timeout_input = QSpinBox()
            self.timeout_input.setRange(1, 300)
            self.timeout_input.setValue(20)
            self.dry_run_input = QCheckBox("Dry run")
            self.dry_run_input.setChecked(True)

            checks = QWidget()
            checks_layout = QHBoxLayout(checks)
            checks_layout.setContentsMargins(0, 0, 0, 0)
            checks_layout.addWidget(self.dry_run_input)

            languages = QWidget()
            languages_layout = QHBoxLayout(languages)
            languages_layout.setContentsMargins(0, 0, 0, 0)
            languages_layout.addWidget(self.english_input)
            languages_layout.addWidget(self.korean_input)

            form.addRow("Title", self.title_input)
            form.addRow("Author", self.author_input)
            form.addRow("Output", out_widget)
            form.addRow("Provider", self.provider_input)
            form.addRow("Language", languages)
            form.addRow("Max results", self.max_results_input)
            form.addRow("Retries", self.retries_input)
            form.addRow("Timeout", self.timeout_input)
            form.addRow("", checks)

            self.run_button = QPushButton("Run")
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.setEnabled(False)
            self.load_button = QPushButton("Load result")
            action_row = QGridLayout()
            action_row.addWidget(self.run_button, 0, 0)
            action_row.addWidget(self.cancel_button, 0, 1)
            action_row.addWidget(self.load_button, 1, 0, 1, 2)
            action_widget = QWidget()
            action_widget.setLayout(action_row)
            form.addRow("", action_widget)

            notice = QLabel(
                "Downloads stay blocked unless license and domain signals are strong. "
                "Manual source review still required."
            )
            notice.setWordWrap(True)
            form.addRow("", notice)

            content = QSplitter()
            content.setOrientation(Qt.Orientation.Vertical)
            self.status_label = QLabel("Idle")
            self.table = QTableWidget(0, 4)
            self.table.setHorizontalHeaderLabels(["Decision", "Score", "PDFs", "Source"])
            self.table.horizontalHeader().setStretchLastSection(True)
            self.detail = QTextEdit()
            self.detail.setReadOnly(True)
            self.log = QTextEdit()
            self.log.setReadOnly(True)

            top = QWidget()
            top_layout = QVBoxLayout(top)
            top_layout.addWidget(self.status_label)
            top_layout.addWidget(self.table)
            top_layout.addWidget(QLabel("Details"))
            top_layout.addWidget(self.detail)
            content.addWidget(top)
            content.addWidget(self.log)
            outer.addWidget(form_panel)
            outer.addWidget(content, 1)

            self.browse_button.clicked.connect(self.choose_output)
            self.run_button.clicked.connect(self.start_run)
            self.cancel_button.clicked.connect(self.cancel_run)
            self.load_button.clicked.connect(self.choose_result)
            self.table.itemSelectionChanged.connect(self.show_selected)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.drain_events)
            self.timer.start(150)

        def settings(self) -> RunSettings:
            return RunSettings(
                title=self.title_input.text(),
                author=self.author_input.text(),
                out_dir=self.out_input.text() or "result",
                max_results=self.max_results_input.value(),
                lang=_language_code(
                    english=self.english_input.isChecked(),
                    korean=self.korean_input.isChecked(),
                ),
                year_from=None,
                year_to=None,
                headless=True,
                dry_run=self.dry_run_input.isChecked(),
                timeout=float(self.timeout_input.value()),
                retries=self.retries_input.value(),
                search_provider=self.provider_input.currentText(),
            )

        def choose_output(self) -> None:
            selected = QFileDialog.getExistingDirectory(self, "Output directory", self.out_input.text())
            if selected:
                self.out_input.setText(selected)

        def choose_result(self) -> None:
            selected, _ = QFileDialog.getOpenFileName(
                self,
                "Open run JSON",
                self.out_input.text() or str(Path.cwd()),
                "Run JSON (run_*.json);;JSON (*.json)",
            )
            if selected:
                self.load_result(Path(selected))

        def start_run(self) -> None:
            try:
                settings = self.settings()
            except ValueError as exc:
                QMessageBox.critical(self, "Invalid input", str(exc))
                return
            errors = validate_settings(settings)
            if errors:
                QMessageBox.critical(self, "Invalid input", "\n".join(errors))
                return

            self.cancel_event = threading.Event()
            self.log_path = Path(settings.out_dir).expanduser() / f"gui_{datetime.now():%Y%m%d_%H%M%S}.log"
            self.clear_results()
            self.set_running(True)
            self.append_log("started")
            self.worker = threading.Thread(target=self.run_worker, args=(settings,), daemon=True)
            self.worker.start()

        def run_worker(self, settings: RunSettings) -> None:
            def progress(event: str, message: str) -> None:
                self.events.put((event, message))

            result = run_crawler(settings, progress_callback=progress, cancel_event=self.cancel_event)
            self.events.put((result.status, str(result.run_path or result.error or "")))

        def cancel_run(self) -> None:
            self.cancel_event.set()
            self.append_log("cancel requested")

        def drain_events(self) -> None:
            while True:
                try:
                    event, message = self.events.get_nowait()
                except queue.Empty:
                    break
                self.status_label.setText(f"{event}: {message}")
                self.append_log(f"{event}: {message}")
                if event in {"completed", "failed", "cancelled"}:
                    self.set_running(False)
                    if event == "completed" and message:
                        self.load_result(Path(message))

        def set_running(self, running: bool) -> None:
            self.run_button.setEnabled(not running)
            self.cancel_button.setEnabled(running)

        def append_log(self, message: str) -> None:
            line = f"{datetime.now():%H:%M:%S} {message}"
            self.log.append(line)
            if self.log_path:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                with self.log_path.open("a", encoding="utf-8") as handle:
                    handle.write(line + "\n")

        def load_result(self, path: Path) -> None:
            try:
                self.current_payload = load_run_file(path)
            except Exception as exc:
                QMessageBox.critical(self, "Load failed", str(exc))
                return
            self.clear_results()
            for row, item in enumerate(self.current_payload.get("results", [])):
                source = item.get("source", {})
                decision = item.get("decision", {})
                values = [
                    decision.get("status", ""),
                    str(source.get("relevance_score", "")),
                    str(len(item.get("candidates", []))),
                    source.get("url", ""),
                ]
                self.table.insertRow(row)
                for col, value in enumerate(values):
                    self.table.setItem(row, col, QTableWidgetItem(value))
            self.status_label.setText(f"Loaded {path}")

        def clear_results(self) -> None:
            self.table.setRowCount(0)
            self.detail.clear()

        def show_selected(self) -> None:
            if not self.current_payload:
                return
            selected = self.table.currentRow()
            if selected < 0:
                return
            result = self.current_payload.get("results", [])[selected]
            self.detail.setPlainText(json.dumps(result, ensure_ascii=False, indent=2))

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


def _language_code(english: bool, korean: bool) -> str:
    if not english and not korean:
        raise ValueError("Select at least one language")
    if english and not korean:
        return "en"
    return "ko"


if __name__ == "__main__":
    raise SystemExit(main())
