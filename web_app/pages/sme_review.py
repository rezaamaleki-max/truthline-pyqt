# File: web_app/pages/sme_review.py
import uuid
from nicegui import ui, app, run
from web_app.config import PAGE_CSS
from web_app.admin_config import is_section_enabled
from web_app.db_manager import save_sme_review
from web_app.data.scenario_metadata import (
    SCENARIOS_METADATA, COMPETENCY_DEFINITIONS, get_full_competency_label
)

@ui.page('/sme-review')
def sme_review_page():
    if not is_section_enabled("sme_review"):
        ui.navigate.to('/')
        return

    ui.query('body').style(PAGE_CSS)
    
    # متغیرهای وضعیت
    state = {
        "expert_name": "",
        "evaluations": {}, # {scenario_id: {clarity: x, ...}}
    }

    # --- هدر صفحه ---
    with ui.row().classes('w-full items-center justify-between p-4 bg-slate-900 border-b border-cyan-500'):
        ui.label("فرم ارزیابی متخصصان (SME)").classes('text-2xl font-bold text-cyan-400')
        # ورودی نام متخصص
        name_input = ui.input(placeholder="نام شما (اختیاری)").classes('bg-slate-800 text-white').props('dark')
        name_input.on_value_change(lambda e: state.update({"expert_name": e.value}))

    # --- چیدمان دو پنلی ---
    splitter = ui.splitter(value=25).classes('w-full h-[calc(100vh-80px)]')
    
    # پنل سمت چپ: لیست سناریوها
    with splitter.before:
        with ui.column().classes('w-full p-2 gap-1 overflow-y-auto h-full bg-slate-900'):
            ui.label("فاز ۱").classes('text-xs font-bold text-orange-400 mt-2')
            scenario_list_container = ui.column().classes('w-full gap-1')
            
            # دکمه‌های سناریو (به صورت پویا ساخته می‌شوند)
            scenario_buttons = {}
            
            def create_scenario_buttons():
                current_phase = 1
                for s in SCENARIOS_METADATA:
                    if s['phase'] != current_phase:
                        current_phase = s['phase']
                        with scenario_list_container: # ✅ استفاده از with
                            ui.label(f"فاز {current_phase}").classes('text-xs font-bold text-orange-400 mt-2')
                    
                    with scenario_list_container: # ✅ استفاده از with
                        btn = ui.button(f"{s['id']}: {s['title']}").classes(
                            'w-full text-right text-xs py-2 bg-slate-800 hover:bg-slate-700'
                        )
                    scenario_buttons[s['id']] = btn

            create_scenario_buttons()

    # پنل سمت راست: فرم ارزیابی
    with splitter.after:
        form_container = ui.column().classes('w-full p-6 h-full overflow-y-auto bg-slate-800')
        
        # تابعی برای بارگذاری یک سناریو در پنل راست
        def load_scenario(scenario_id):
            form_container.clear()
            scenario = next((s for s in SCENARIOS_METADATA if s['id'] == scenario_id), None)
            if not scenario:
                return

            # برجسته کردن دکمه‌ی انتخاب شده
            for sid, btn in scenario_buttons.items():
                btn.classes(replace='w-full text-right text-xs py-2 bg-slate-800 hover:bg-slate-700')
            scenario_buttons[scenario_id].classes(replace='w-full text-right text-xs py-2 bg-cyan-800 hover:bg-cyan-700 font-bold')

            with form_container:
                # ۱. خلاصه سناریو و شایستگی
                with ui.card().classes('w-full bg-slate-900 border border-cyan-700 p-4 mb-4'):
                    ui.label(f"سناریو {scenario['id']} - {scenario['title']}").classes('text-xl font-bold text-white mb-2')
                    ui.label(scenario['summary']).classes('text-sm text-gray-300 leading-relaxed mb-4 text-justify')
                    
                    comp_label = get_full_competency_label(scenario)
                    comp_key = scenario['competency']
                    short_def = COMPETENCY_DEFINITIONS.get(comp_key, {}).get('short_def', '')
                    
                    ui.label(f"🎯 شایستگی هدف: {comp_label}").classes('text-sm font-bold text-cyan-400 mt-2')
                    ui.label(f"تعریف: {short_def}").classes('text-xs text-gray-400')

                # ۲. فرم امتیازدهی
                with ui.card().classes('w-full bg-slate-900 border border-slate-700 p-4'):
                    ui.label("ارزیابی شما (۱ = بسیار ضعیف، ۵ = بسیار خوب)").classes('text-sm text-orange-400 mb-4')
                    
                    def make_rating_row(label_text, key):
                        with ui.row().classes('w-full items-center justify-between mb-2'):
                            ui.label(label_text).classes('text-sm text-white w-1/3')
                            rb = ui.radio([1, 2, 3, 4, 5], value=None).props('inline').classes('text-white')
                            return rb
                        
                    rb_clarity = make_rating_row("وضوح (Clarity):", "clarity")
                    rb_realism = make_rating_row("واقع‌گرایی (Realism):", "realism")
                    rb_cultural = make_rating_row("تناسب فرهنگی:", "cultural_fit")
                    rb_comp = make_rating_row("تطابق با شایستگی:", "competency_match")
                    rb_essential = make_rating_row("ضرورت (Essentiality):", "essentiality")

                    # کادر نظر
                    ui.label("پیشنهاد/اصلاح (اختیاری):").classes('text-sm text-gray-400 mt-4 mb-1')
                    comment_input = ui.textarea().classes('w-full bg-slate-800 text-white text-sm').props('dark')

                    # دکمه ثبت
                    async def submit_review():
                        # اعتبارسنجی
                        if not all([rb_clarity.value, rb_realism.value, rb_cultural.value, rb_comp.value, rb_essential.value]):
                            ui.notify("لطفاً به همه‌ی ۵ معیار امتیاز دهید.", type='warning', position='top')
                            return

                        expert_id = app.storage.user.get('participant_id', str(uuid.uuid4())[:8])
                        expert_name = state['expert_name'] or "ناشناس"
                        
                        success = await run.io_bound(
                            save_sme_review,
                            expert_id=expert_id,
                            expert_name=expert_name,
                            scenario_id=scenario['id'],
                            clarity=rb_clarity.value,
                            realism=rb_realism.value,
                            cultural_fit=rb_cultural.value,
                            competency_match=rb_comp.value,
                            essentiality=rb_essential.value,
                            comment=(comment_input.value or "").strip() # ✅ اصلاح شد
                        )
                        if success:
                            ui.notify(f"✓ ارزیابی سناریوی {scenario['id']} ثبت شد.", type='positive', position='top')
                            # پاک کردن فرم برای ارزیابی بعدی
                            rb_clarity.set_value(None)
                            rb_realism.set_value(None)
                            rb_cultural.set_value(None)
                            rb_comp.set_value(None)
                            rb_essential.set_value(None)
                            comment_input.set_value("")
                            # رفتن به سناریوی بعدی (اختیاری)
                            next_idx = SCENARIOS_METADATA.index(scenario) + 1
                            if next_idx < len(SCENARIOS_METADATA):
                                load_scenario(SCENARIOS_METADATA[next_idx]['id'])
                        else:
                            ui.notify("خطا در ذخیره‌سازی.", type='negative', position='top')

                    ui.button("ثبت ارزیابی این سناریو", on_click=submit_review).classes(
                        'w-full mt-4 py-3 bg-green-600 hover:bg-green-500 text-lg font-bold rounded-lg'
                    )

        # اتصال دکمه‌ها به تابع بارگذاری
        for s in SCENARIOS_METADATA:
            scenario_buttons[s['id']].on_click(lambda sid=s['id']: load_scenario(sid))

        # بارگذاری پیش‌فرض اولین سناریو
        if SCENARIOS_METADATA:
            load_scenario(SCENARIOS_METADATA[0]['id'])