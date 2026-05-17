# PDF Tools Desktop UI Stable Workbench Design

## Goal

Optimize the PySide6 desktop application into a restrained, stable, government and enterprise style workbench. The interface should feel clear, professional, and reliable while preserving the existing PDF processing behavior.

## Scope

This design applies only to the `pdf-tools` desktop program.

In scope:

- `MainWindow` navigation and application shell.
- Authorization center layout and status presentation.
- PDF tool pages in `pdf_tools/pages/`.
- Shared desktop UI components for repeated patterns such as file drop areas, path rows, page headers, action bars, and status feedback.
- Visual consistency, Chinese display text, spacing, button hierarchy, and maintainability.

Out of scope:

- Website or account portal changes in `pdf-tools-home-trae`.
- New PDF processing features.
- Changes to worker thread behavior except where required to connect existing status signals to the refreshed UI.
- Replacing PySide6 with QML or another frontend framework.

## Design Direction

Use the approved "stable workbench" direction:

- Dark left sidebar for durable navigation.
- Light content workspace for document operations.
- Conservative blue-gray palette.
- Clear primary and secondary button hierarchy.
- Moderate information density suitable for repeated office work.
- No decorative gradients, oversized marketing layout, or playful visual treatment.

## Application Shell

The main window remains a `QMainWindow` with a horizontal layout:

- Left navigation: fixed-width sidebar with app name, grouped tool entries, selected state, and subtle hover state.
- Right workspace: stacked pages with consistent background and margins.
- Window title and icon remain unchanged.
- Default window size should be more comfortable than the current half-screen sizing, while still adapting to available screen geometry.

Navigation labels should use readable Chinese text:

- 授权中心
- PDF 合并
- PDF 分割
- PDF 压缩
- PDF 转 Word
- PDF 转 PPT
- PDF 转 Excel
- PDF 转图片
- PDF 加密

## Page Template

Each functional page should follow the same structure:

1. Page header: title plus one short description of the task.
2. Input area: file drop or file list area with click and drag support.
3. Parameters area: tool-specific settings such as split page count, page range, password, or filename.
4. Output area: output path or folder selection and open-file/open-folder action.
5. Action area: progress/status on the left and the primary operation button on the right.

This template should be implemented through reusable helper widgets or builder functions so future pages do not duplicate layout code.

## Shared Components

Create shared UI helpers under `pdf_tools/`, for example `ui_components.py` and `theme.py`.

Expected shared pieces:

- `DropArea`: a reusable PDF file selector with click and drag behavior, selected-file styling, file size display, and path display.
- Page header helper: consistent title and subtitle styling.
- Section container helper: consistent margins and optional title.
- Path row helper: label, read-only path field, choose button, and open button.
- Action row helper: progress indicator, status text, and primary button placement.
- Theme or stylesheet function: central source for colors, spacing, buttons, inputs, list widgets, and message surfaces.

The shared components should preserve existing page behavior while removing duplicated `DropArea` definitions across pages.

## Authorization Center

The authorization page should be presented as a status-oriented panel rather than a plain vertical form.

Structure:

- Header: 授权中心 with a short explanation.
- Status card: 已授权 or 未授权, using clear but restrained color.
- Device card: device fingerprint with copyable/readable layout if practical.
- Binding card: current binding code, confirmation state, and polling status.
- Action row: 生成在线绑定码, 打开网页确认, 导入离线 License, 刷新状态.

The existing authorization functions remain the source of truth:

- `get_authorization_status`
- `get_device_fingerprint`
- `start_device_binding`
- `poll_device_binding`
- `import_offline_license`

## Tool Pages

Each page keeps its existing workflow and thread classes.

PDF merge:

- Use a file list as the input area.
- Keep add, remove, move up, and move down actions.
- Show output PDF path and open-file action.
- Primary action: 开始合并.

Single-input tools such as split, compress, encrypt, convert to Word, convert to PPT, convert to image, and convert to Excel:

- Use the shared `DropArea`.
- Keep existing tool-specific options.
- Show output file or output folder in a consistent output section.
- Primary action text should match the operation.

PDF to Excel is currently not implemented. It should receive the same visual shell and remain honest about implementation status rather than implying the conversion is complete.

## Error Handling And Status

Existing `QMessageBox` success and error messages can remain for this iteration. Pages should also expose lightweight inline status where practical:

- Ready state before input.
- Processing state while a thread runs.
- Completed state with output path.
- Failed state with a concise error message.

Buttons that start processing should be disabled while work is running, matching current behavior.

## Testing And Verification

Verification should cover:

- The application imports without syntax errors.
- The GUI entry point starts successfully in a local desktop environment when available.
- Existing authorization tests continue to pass.
- Reused `DropArea` still supports click selection, drag-and-drop, and selected-file display.
- Main pages can be instantiated without starting background work.

If GUI execution cannot be verified in the current environment, the implementation should still run Python import or compile checks and report the limitation.

## Non-Goals

- No new licensing model.
- No subscription or payment UI changes.
- No website design changes.
- No new PDF conversion algorithms.
- No large architectural rewrite beyond extracting shared UI components needed for this UI cleanup.
