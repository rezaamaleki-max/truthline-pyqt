"""
ابزارهای کمکی RTL — نسخه PyQt6
================================
این فایل مشکلات رایج RTL را حل می‌کند:
- متن داخل QLineEdit / QTextEdit / QSpinBox / QComboBox
- چیدمان محتوای QScrollArea
- لیبل‌های غیرِ وسط‌چین
- QMessageBoxها
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QScrollArea, QMessageBox, QBoxLayout,
)

RTL = Qt.LayoutDirection.RightToLeft
_ALIGN_R = Qt.AlignmentFlag.AlignRight
_ALIGN_RV = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_ALIGN_RT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
_ALIGN_C = Qt.AlignmentFlag.AlignHCenter


# ============================================================
# ۱. RTL سراسری روی QApplication — یک بار در main()
# ============================================================
def enable_rtl_app() -> None:
    """
    جهت کل اپلیکیشن را راست‌به‌چپ می‌کند.
    باید بلافاصله بعد از ساخت QApplication صدا زده شود.
    """
    QApplication.setLayoutDirection(RTL)


# ============================================================
# ۲. QMessageBox راست‌چین
# ============================================================
def rtl_message_box(msg: QMessageBox) -> QMessageBox:
    """QMessageBox را راست‌چین می‌کند."""
    if msg is not None:
        msg.setLayoutDirection(RTL)
    return msg


# ============================================================
# ۳. راست‌چین کردن متن داخل همه‌ی ویجت‌های ورودی
# ============================================================
def fix_inputs(root: QWidget) -> None:
    """
    متن داخل تمام ویجت‌های ورودی زیرمجموعه‌ی root را
    راست‌چین می‌کند.
    """
    if root is None:
        return

    # QLineEdit (شامل lineEdit داخلی ComboBox هم می‌شود)
    for w in root.findChildren(QLineEdit):
        w.setAlignment(_ALIGN_RV)

    # QTextEdit — این کلاس متد setAlignment دارد
    for w in root.findChildren(QTextEdit):
        w.setAlignment(_ALIGN_RT)

    # QPlainTextEdit — setAlignment ندارد، از document استفاده می‌کنیم
    for w in root.findChildren(QPlainTextEdit):
        _set_plaintext_edit_alignment(w)

    # QSpinBox / QDoubleSpinBox
    for w in root.findChildren(QSpinBox):
        w.setAlignment(_ALIGN_RV)
    for w in root.findChildren(QDoubleSpinBox):
        w.setAlignment(_ALIGN_RV)

    # QComboBox: lineEdit داخلی (اگر editable باشد)
    for w in root.findChildren(QComboBox):
        w.setLayoutDirection(RTL)
        le = w.lineEdit()
        if le is not None:
            le.setAlignment(_ALIGN_RV)


def _set_plaintext_edit_alignment(w: QPlainTextEdit) -> None:
    """
    راست‌چین کردن متن QPlainTextEdit از طریق QTextOption.
    این کلاس متد setAlignment ندارد؛ باید از document استفاده کرد.
    """
    try:
        from PyQt6.QtGui import QTextOption
        doc = w.document()
        if doc is None:
            return
        opt = QTextOption()
        opt.setAlignment(Qt.AlignmentFlag.AlignRight)
        doc.setDefaultTextOption(opt)
    except Exception:
        pass


# ============================================================
# ۴. راست‌چین کردن لیبل‌های غیرِ وسط‌چین
# ============================================================
def fix_labels(root: QWidget) -> None:
    """
    همه‌ی QLabelهایی که وسط‌چین نشده‌اند را راست‌چین می‌کند.
    در RTL، «AlignLeft» = leading = سمت راست فیزیکی.
    """
    if root is None:
        return
    for w in root.findChildren(QLabel):
        current = w.alignment()
        # اگر وسط‌چین است، دست نزن
        if current & _ALIGN_C:
            continue
        # ✅ در RTL از AlignLeft استفاده کن
        w.setLayoutDirection(RTL)
        w.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

# ============================================================
# ۵. رفع RTL در QScrollArea و محتوای آن
# ============================================================
def fix_scroll_areas(root: QWidget) -> None:
    """
    تضمین می‌کند که هم QScrollArea و هم ویجت داخلی‌اش
    (که جدای از parent رفتار می‌کند) RTL باشند.
    """
    if root is None:
        return
    for sa in root.findChildren(QScrollArea):
        sa.setLayoutDirection(RTL)
        inner = sa.widget()
        if inner is not None:
            inner.setLayoutDirection(RTL)


# ============================================================
# ۶. تابع تجمیعی — در انتهای __init__ هر Scene
# ============================================================
def apply_rtl_fixes(scene: QWidget) -> None:
    if scene is None:
        return
    scene.setLayoutDirection(RTL)
    fix_scroll_areas(scene)
    fix_inputs(scene)
    fix_labels(scene)

    # ✅ پردازش محتوای QScrollArea جداگانه
    from PyQt6.QtWidgets import QScrollArea
    for sa in scene.findChildren(QScrollArea):
        inner = sa.widget()
        if inner is not None:
            inner.setLayoutDirection(RTL)
            fix_labels(inner)
            fix_inputs(inner)


# ============================================================
# ۷. کمکی برای ردیف رادیو-باتن‌های Likert
# ============================================================
def rtl_radio_row(layout: QBoxLayout) -> None:
    """
    یک QHBoxLayout حاوی QRadioButton را برای RTL آماده می‌کند.
    ⚠️ بعد از صدا زدن این تابع، باید addStretch() را
    در **انتهای** layout صدا بزنی (نه ابتدا).
    """
    if layout is not None:
        layout.setDirection(QBoxLayout.Direction.RightToLeft)