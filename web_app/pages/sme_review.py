# File: web_app/pages/sme_review.py
import uuid
from nicegui import ui, app, run
from web_app.config import PAGE_CSS
from web_app.admin_config import is_section_enabled, load_admin_config
from web_app.db_manager import save_sme_review, save_sme_expert_profile
from web_app.data.scenario_metadata import (
    SCENARIOS_METADATA, COMPETENCY_DEFINITIONS, get_full_competency_label
)

@ui.page('/sme-review')
def sme_review_page():
    if not is_section_enabled("sme_review"):
        ui.navigate.to('/')
        return

    ui.query('body').style(PAGE_CSS)
    
    # مقداردهی اولیه وضعیت در نشست مرورگر
    if 'sme_evaluated' not in app.storage.user:
        app.storage.user['sme_evaluated'] = []

    # ==========================================
    # بخش ۱: احراز هویت و فرم مشخصات
    # ==========================================
    if not app.storage.user.get('sme_profile'):
        with ui.column().classes('w-full h-screen items-center justify-center bg-slate-900'):
            with ui.card().classes('p-8 bg-slate-800 border-2 border-cyan-500 rounded-xl shadow-2xl w-[500px]'):
                ui.label("🔒 ورود و مشخصات متخصص").classes('text-2xl font-bold text-cyan-400 mb-4 text-center w-full')
                
                # اگر رمز را وارد نکرده است
                if not app.storage.user.get('sme_authenticated'):
                    pwd_input = ui.input(
                        placeholder="رمز عبور را وارد کنید", 
                        password=True, 
                        password_toggle_button=True
                    ).classes('w-full text-lg bg-slate-700 text-white').props('dark')
                    
                    def check_password():
                        cfg = load_admin_config()
                        correct_pwd = cfg.get("sme_password", "expert-2026")
                        if pwd_input.value == correct_pwd:
                            app.storage.user['sme_authenticated'] = True
                            ui.navigate.to('/sme-review')
                        else:
                            ui.notify("رمز عبور نادرست است.", type='negative', position='top')
                    
                    ui.button("تأیید رمز", on_click=check_password).classes(
                        'w-full mt-4 bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-2 rounded'
                    )
                    pwd_input.on('keydown.enter', check_password)
                
                # اگر رمز درست بود، فرم مشخصات را نشان بده
                else:
                    ui.label("لطفاً مشخصات خود را وارد کنید (الزامی):").classes('text-sm text-orange-400 mb-2')
                    
                    name_input = ui.input(label="نام و نام خانوادگی").classes('w-full').props('dark')
                    edu_input = ui.select(
                        ["کارشناسی", "کارشناسی ارشد", "دکتری", "پسادکتری"], 
                        label="مقطع تحصیلی"
                    ).classes('w-full').props('dark')
                    job_input = ui.input(label="شغل فعلی (سازمان/دانشگاه)").classes('w-full').props('dark')
                    contact_input = ui.input(label="راه ارتباطی (ایمیل یا شماره تماس) - اختیاری").classes('w-full').props('dark')

                    async def submit_profile():
                        if not name_input.value or not edu_input.value or not job_input.value:
                            ui.notify("لطفاً فیلدهای نام، تحصیلات و شغل را تکمیل کنید.", type='warning', position='top')
                            return
                        
                        expert_id = app.storage.user.get('participant_id')
                        if not expert_id:
                            expert_id = str(uuid.uuid4())[:8]
                            app.storage.user['participant_id'] = expert_id
                        
                        success = await run.io_bound(
                            save_sme_expert_profile,
                            expert_id=expert_id,
                            name=name_input.value.strip(),
                            education=edu_input.value,
                            current_job=job_input.value.strip(),
                            contact_info=(contact_input.value or "").strip()
                        )
                        if success:
                            app.storage.user['sme_profile'] = {
                                "name": name_input.value.strip(),
                                "education": edu_input.value,
                                "current_job": job_input.value.strip()
                            }
                            ui.navigate.to('/sme-review')
                        else:
                            ui.notify("خطا در ذخیره اطلاعات.", type='negative')

                    ui.button("ورود به پنل ارزیابی", on_click=submit_profile).classes(
                        'w-full mt-4 bg-green-600 hover:bg-green-500 text-white font-bold py-2 rounded'
                    )
        return

    # ==========================================
    # بخش ۲: پنل اصلی ارزیابی
    # ==========================================
    expert_id = app.storage.user.get('participant_id')
    profile = app.storage.user.get('sme_profile')
    evaluated_list = app.storage.user.get('sme_evaluated', [])

    # ✅ بررسی امنیتی برای Pylance (اگر به هر دلیلی مقدار نداشتند، برگرد به صفحه ورود)
    if not expert_id or not profile:
        app.storage.user['sme_authenticated'] = False
        app.storage.user['sme_profile'] = None
        ui.navigate.to('/sme-review')
        return

    # --- هدر صفحه ---
    with ui.row().classes('w-full items-center justify-between p-4 bg-slate-900 border-b border-cyan-500'):
        ui.label(f"ارزیابی متخصصان - {profile['name']} ({profile['education']})").classes('text-xl font-bold text-cyan-400')
        
        def show_logout_dialog():
            total = len(SCENARIOS_METADATA)
            evaluated = len(evaluated_list)
            remaining = total - evaluated
            
            with ui.dialog() as dialog, ui.card().classes('p-6 bg-slate-800 text-white w-[400px]'):
                ui.label("گزارش پیشرفت شما").classes('text-xl font-bold text-cyan-400 mb-4')
                ui.label(f"شما تاکنون به {evaluated} سناریو از {total} سناریو امتیاز داده‌اید.").classes('text-sm mb-2')
                
                if remaining > 0:
                    ui.label(f"هنوز {remaining} سناریو باقی مانده است. آیا می‌خواهید ادامه دهید یا خارج شوید؟").classes('text-sm text-orange-400 mb-4')
                    with ui.row().classes('w-full justify-end gap-2'):
                        ui.button("ادامه ارزیابی", on_click=dialog.close).classes('bg-cyan-600 hover:bg-cyan-500')
                        def do_logout():
                            app.storage.user['sme_profile'] = None
                            app.storage.user['sme_authenticated'] = False
                            app.storage.user['sme_evaluated'] = []
                            dialog.close()
                            ui.navigate.to('/sme-review')
                        ui.button("خروج", on_click=do_logout).classes('bg-red-600 hover:bg-red-500')
                else:
                    ui.label("شما به همه سناریوها امتیاز داده‌اید. از همکاری شما سپاسگزاریم!").classes('text-sm text-green-400 mb-4')
                    def do_logout_final():
                        app.storage.user['sme_profile'] = None
                        app.storage.user['sme_authenticated'] = False
                        app.storage.user['sme_evaluated'] = []
                        dialog.close()
                        ui.navigate.to('/sme-review')
                    ui.button("خروج نهایی", on_click=do_logout_final).classes('w-full bg-green-600 hover:bg-green-500')
            dialog.open()
            
        ui.button("خروج", on_click=show_logout_dialog).classes('bg-red-600 hover:bg-red-500 text-white text-sm py-1 px-4 rounded')

    # --- چیدمان دو پنلی ---
    splitter = ui.splitter(value=25).classes('w-full h-[calc(100vh-80px)]')
    
    # پنل سمت چپ: لیست سناریوها
    with splitter.before:
        with ui.column().classes('w-full p-2 gap-1 overflow-y-auto h-full bg-slate-900'):
            scenario_buttons = {}
            
            def refresh_scenario_buttons():
                for s in SCENARIOS_METADATA:
                    is_done = s['id'] in app.storage.user.get('sme_evaluated', [])
                    text = f"✓ {s['id']}: {s['title']}" if is_done else f"{s['id']}: {s['title']}"
                    if s['id'] in scenario_buttons:
                        scenario_buttons[s['id']].set_text(text)
                        if is_done:
                            scenario_buttons[s['id']].classes(add='text-green-400')
                        else:
                            scenario_buttons[s['id']].classes(remove='text-green-400')

            current_phase = 1
            for s in SCENARIOS_METADATA:
                if s['phase'] != current_phase:
                    current_phase = s['phase']
                    ui.label(f"فاز {current_phase}").classes('text-xs font-bold text-orange-400 mt-2')
                
                is_done = s['id'] in evaluated_list
                text = f"✓ {s['id']}: {s['title']}" if is_done else f"{s['id']}: {s['title']}"
                btn = ui.button(text).classes(
                    f'w-full text-right text-xs py-2 bg-slate-800 hover:bg-slate-700 {"text-green-400" if is_done else ""}'
                )
                scenario_buttons[s['id']] = btn

    # پنل سمت راست: فرم ارزیابی
    with splitter.after:
        form_container = ui.column().classes('w-full p-6 h-full overflow-y-auto bg-slate-800')
        
        def load_scenario(scenario_id):
            form_container.clear()
            scenario = next((s for s in SCENARIOS_METADATA if s['id'] == scenario_id), None)
            if not scenario:
                return

            # برجسته کردن دکمه انتخاب‌شده
            for sid, btn in scenario_buttons.items():
                btn.classes(replace='w-full text-right text-xs py-2 bg-slate-800 hover:bg-slate-700')
                if sid in app.storage.user.get('sme_evaluated', []):
                    btn.classes(add='text-green-400')
            
            scenario_buttons[scenario_id].classes(replace='w-full text-right text-xs py-2 bg-cyan-800 hover:bg-cyan-700 font-bold')
            if scenario_id in app.storage.user.get('sme_evaluated', []):
                scenario_buttons[scenario_id].classes(add='text-green-400')

            with form_container:
                # ۱. خلاصه سناریو
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

                    ui.label("پیشنهاد/اصلاح (اختیاری):").classes('text-sm text-gray-400 mt-4 mb-1')
                    comment_input = ui.textarea().classes('w-full bg-slate-800 text-white text-sm').props('dark')

                    async def submit_review():
                        if not all([rb_clarity.value, rb_realism.value, rb_cultural.value, rb_comp.value, rb_essential.value]):
                            ui.notify("لطفاً به همه‌ی ۵ معیار امتیاز دهید.", type='warning', position='top')
                            return

                        success = await run.io_bound(
                            save_sme_review,
                            expert_id=expert_id,
                            expert_name=profile['name'],
                            scenario_id=scenario['id'],
                            clarity=rb_clarity.value,
                            realism=rb_realism.value,
                            cultural_fit=rb_cultural.value,
                            competency_match=rb_comp.value,
                            essentiality=rb_essential.value,
                            comment=(comment_input.value or "").strip()
                        )
                        if success:
                            ui.notify(f"✓ ارزیابی سناریوی {scenario['id']} ثبت شد.", type='positive', position='top')
                            
                            # ✅ افزودن به لیست ارزیابی‌شده‌ها و به‌روزرسانی تیک
                            evaluated = app.storage.user.get('sme_evaluated', [])
                            if scenario['id'] not in evaluated:
                                evaluated.append(scenario['id'])
                                app.storage.user['sme_evaluated'] = evaluated
                            
                            refresh_scenario_buttons()
                            
                            # رفتن به سناریوی بعدی
                            next_idx = SCENARIOS_METADATA.index(scenario) + 1
                            if next_idx < len(SCENARIOS_METADATA):
                                load_scenario(SCENARIOS_METADATA[next_idx]['id'])
                        else:
                            ui.notify("خطا در ذخیره‌سازی.", type='negative', position='top')

                    ui.button("ثبت ارزیابی و رفتن به سناریوی بعد", on_click=submit_review).classes(
                        'w-full mt-4 py-3 bg-green-600 hover:bg-green-500 text-lg font-bold rounded-lg'
                    )

        # اتصال دکمه‌ها
        for s in SCENARIOS_METADATA:
            scenario_buttons[s['id']].on_click(lambda sid=s['id']: load_scenario(sid))

        # بارگذاری اولین سناریوی ارزیابی‌نشده
        first_unreviewed = next((s['id'] for s in SCENARIOS_METADATA if s['id'] not in evaluated_list), SCENARIOS_METADATA[0]['id'])
        load_scenario(first_unreviewed)