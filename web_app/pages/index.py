"""صفحه‌ی خوش‌آمد"""
from nicegui import ui, app
from web_app.config import PAGE_CSS
from web_app.db_manager import get_participant
from web_app.components.audio_control import setup_page_audio


@ui.page('/')
def index_page():
    # اگر کاربر قبلاً ثبت‌نام کرده، به فاز ۱ برود
    if app.storage.user.get('participant_id'):
        participant = get_participant(app.storage.user['participant_id'])
        if participant:
            ui.navigate.to('/phase1')
            return
        else:
            # ✅ کوکی منقضی است — پاک کن
            app.storage.user.clear()

    setup_page_audio("menu")

    ui.query('body').style(PAGE_CSS)

    with ui.column().classes('w-full max-w-3xl mx-auto p-12 items-center gap-6'):
        ui.label('TRUTHLINE').classes('text-6xl font-bold text-cyan-400 mt-16')
        ui.label('بحران ایستگاه کاسپین').classes('text-2xl text-white')
        ui.separator().classes('w-64 my-4')
        ui.label(
            'به پژوهش حاضر خوش آمدید. این یک بازی تصمیم‌گیری در محیطی شبیه‌سازی‌شده است '
            'که بخشی از یک رساله دکتری در حوزه ارزیابی ویژگی‌های شخصیتی با استفاده از '
            'بازی‌های جدی (Serious Games) می‌باشد. لطفاً با دقت و در فضایی آرام به '
            'موقعیت‌ها پاسخ دهید. در پایان، گزارش جامعی از ویژگی‌های ارزیابی‌شده خود '
            'دریافت خواهید کرد تا بتوانید نتایج خود را با دیگران مقایسه کنید.'
        ).classes('text-base text-gray-300 text-center max-w-2xl leading-relaxed')

        with ui.card().classes('w-full bg-slate-800 border border-cyan-400 p-6 mt-6'):
            ui.label('📋 راهنما').classes('text-xl font-bold text-cyan-400 mb-3')
            with ui.column().classes('gap-2 text-gray-300'):
                ui.label('• مدت زمان تقریبی: ۳۰ تا ۴۵ دقیقه').classes('text-base')
                ui.label('• داده‌های شما به صورت محرمانه تحلیل می‌شود').classes('text-base')
                ui.label('• می‌توانید هر زمان که خواستید انصراف دهید').classes('text-base')

        ui.button(
            'شروع',
            on_click=lambda: ui.navigate.to('/demographic'),
        ).classes(
            'bg-cyan-600 hover:bg-cyan-500 text-white '
            'text-xl font-bold py-4 px-16 mt-6 rounded-lg'
        )

        # ✅ لینک ورود متخصصان (SME) با هشدار بصری
        from web_app.admin_config import is_section_enabled
        if is_section_enabled("sme_review"):
            with ui.column().classes('w-full items-center gap-2 mt-8'):
                # خط جداکننده
                ui.element('div').classes('w-64 h-px bg-slate-700 my-2')
                
                ui.button(
                    '🧑‍🔬 ورود متخصصان (پس از انجام بازی)',
                    on_click=lambda: ui.navigate.to('/sme-review'),
                ).classes(
                    'bg-slate-800 hover:bg-slate-700 border border-slate-600 text-sm py-2 px-6 rounded-lg text-gray-300'
                )
                ui.label(
                    "توجه متخصصان گرامی: لطفاً ابتدا بازی را انجام دهید "
                    "و سپس فرم ارزیابی سناریوها (SME) را تکمیل نمایید."
                ).classes(
                    'text-xs text-orange-400 text-center max-w-md leading-relaxed'
                )