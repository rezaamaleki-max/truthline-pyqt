"""
پرونده‌ی شخصیت‌ها — اطلاعات تدریجی درباره لی، رحیمی، آرتمیس
- کاملاً لایه‌ی روایی — هیچ نمره‌ای در آن نیست
- هر یادداشت یک شرط باز شدن دارد
- در حالت Short هم کار می‌کند

نسخه: 1.0.0
"""

# ============================================================
# پروفایل شخصیت‌ها
# ============================================================
CHARACTER_PROFILES = {
    # ==========================================================
    # لی — کارآموز بخش ناوبری
    # ==========================================================
    "li": {
        "name": "لی",
        "role": "کارآموز بخش ناوبری",
        "icon": "👤",
        "color": "#4CAF50",
        "notes": [
            {
                "id": "li_base",
                "condition": {"type": "always"},
                "text": (
                    "کارآموز بخش ناوبری. سه ماه پیش به ایستگاه آمده. "
                    "باانگیزه، ولی بی‌تجربه. مهندس رحیمی از او "
                    "تعریف می‌کند."
                ),
            },
            {
                "id": "li_memory_module",
                "condition": {"type": "after_scenario",
                              "value": "MC-01"},
                "text": (
                    "یک ماژول حافظه از انبار برداشته بود برای "
                    "پروژه‌ی شخصی. با شما در میان گذاشت — چیزی که "
                    "نشان می‌دهد به شما اعتماد داشت."
                ),
            },
            {
                "id": "li_algorithm",
                "condition": {"type": "after_scenario",
                              "value": "F-02"},
                "text": (
                    "ادعا می‌کند الگوریتم کالیبراسیون را خودش طراحی "
                    "کرده. دفترچه‌ی یادداشتش تاریخ ثبت دارد. "
                    "سابقه‌ی او در دفترچه، جدی و دقیق است."
                ),
            },
            {
                "id": "li_sister",
                "condition": {"type": "after_scenario",
                              "value": "BC-01"},
                "text": (
                    "خواهر بیماری دارد که به دارو نیاز دارد. "
                    "همین دلیل، درخواست اعتبار ویژه از شما کرد. "
                    "خانواده‌اش در بخش دیگری از شبکه زندگی می‌کنند."
                ),
            },
            {
                "id": "li_pressure",
                "condition": {"type": "after_scenario",
                              "value": "BC-02"},
                "text": (
                    "در یک اشتباه محاسباتی، نگران آینده‌ی شغلی‌اش "
                    "شد. ترس از دست دادن موقعیت، برای او انگیزه‌ای "
                    "قوی است."
                ),
            },
            {
                "id": "li_feedback",
                "condition": {"type": "after_scenario",
                              "value": "RG-01"},
                "text": (
                    "در ارزیابی ۳۶۰ درجه، سبک مدیریت شما را "
                    "«انگیزه‌کش» توصیف کرد و از احساس تنهایی در "
                    "لحظات بحرانی نوشت."
                ),
            },
            {
                "id": "li_warm",
                "condition": {"type": "relationship_gte",
                              "value": 2},
                "text": (
                    "در طول مأموریت، به شما اعتماد کرده است. "
                    "نظرش را با شما در میان گذاشته و در تصمیم‌های "
                    "دشوار، به حمایت شما تکیه کرده."
                ),
            },
            {
                "id": "li_cold",
                "condition": {"type": "relationship_lte",
                              "value": -1},
                "text": (
                    "از شما فاصله گرفته است. در تعاملات، سرد و "
                    "کوتاه صحبت می‌کند و از درخواست کمک مستقیم "
                    "پرهیز می‌کند."
                ),
            },
        ],
    },

    # ==========================================================
    # مهندس رحیمی — مسئول نگهداری
    # ==========================================================
    "rahimi": {
        "name": "مهندس رحیمی",
        "role": "مسئول نگهداری ایستگاه",
        "icon": "🔧",
        "color": "#FF8F00",
        "notes": [
            {
                "id": "rahimi_base",
                "condition": {"type": "always"},
                "text": (
                    "بیست سال سابقه‌ی خدمت در ایستگاه کاسپین. "
                    "مسئول نگهداری همه‌ی سیستم‌های ایستگاه. "
                    "معمولاً آرام و کوتاه صحبت می‌کند."
                ),
            },
            {
                "id": "rahimi_calibration",
                "condition": {"type": "after_scenario",
                              "value": "DA-01"},
                "text": (
                    "در کالیبراسیون، به شما گفت که «هر جور "
                    "راحت‌تری» انجامش بدهید. این جمله، الگوی "
                    "کار او را نشان می‌دهد: ترجیح راه‌حل‌های "
                    "سریع."
                ),
            },
            {
                "id": "rahimi_quantum",
                "condition": {"type": "after_scenario",
                              "value": "VH-01"},
                "text": (
                    "در بحران کوانتومی، از شما خواست که داده‌ی "
                    "امن گزارش کنید. از قرنطینه‌ی ایستگاه "
                    "می‌ترسید — نه فقط به خاطر شغلش، بلکه به "
                    "خاطر خدمه."
                ),
            },
            {
                "id": "rahimi_side_project",
                "condition": {"type": "after_scenario",
                              "value": "MC-02"},
                "text": (
                    "پروژه‌ی جانبی برای بهبود بازدهی خنک‌کننده "
                    "داشت که به‌صورت غیرمجاز اجرا کرد. وقتی "
                    "افشا شد، به شما گفت: «بیست سال این‌جام. "
                    "اگه این موضوع فاش بشه، پرونده‌ام بسته "
                    "می‌شه.»"
                ),
            },
            {
                "id": "rahimi_insulation",
                "condition": {"type": "after_scenario",
                              "value": "TR-01"},
                "text": (
                    "در نقص عایق سوخت، از شما خواست که صبر "
                    "کنید و اول او بررسی کند. ترجیح می‌دهد "
                    "مسائل را درون‌تیمی حل کند، نه از طریق "
                    "مرکز."
                ),
            },
            {
                "id": "rahimi_advocate",
                "condition": {"type": "relationship_gte",
                              "value": 2},
                "text": (
                    "در جلسه‌ی شورا، به نفع شما صحبت کرد. "
                    "گفت: «توی این چهار روز، من بارها دیدم که "
                    "تو راهی رفتی که من از خودم انتظار نداشتم.»"
                ),
            },
            {
                "id": "rahimi_critic",
                "condition": {"type": "relationship_lte",
                              "value": -2},
                "text": (
                    "نظرات انتقادی خود را درباره‌ی شیوه‌ی کار شما "
                    "به شورا ارائه داده است. رابطه‌ی شما با "
                    "او، به سردی گراییده."
                ),
            },
        ],
    },

    # ==========================================================
    # دکتر آرتمیس — تحلیلگر داده
    # ==========================================================
    "artemis": {
        "name": "دکتر آرتمیس",
        "role": "مسئول تحلیل داده‌های علمی",
        "icon": "🔬",
        "color": "#9C27B0",
        "notes": [
            {
                "id": "artemis_base",
                "condition": {"type": "always"},
                "text": (
                    "مسئول تحلیل داده‌های علمی ایستگاه. یکی از "
                    "دقیق‌ترین تحلیلگران شبکه. در لحظه‌های اول، "
                    "به شما گفت که روی چند آنومالی در داده‌های "
                    "هفته‌ی گذشته کار می‌کند."
                ),
            },
            {
                "id": "artemis_scientific",
                "condition": {"type": "after_scenario",
                              "value": "TR-01"},
                "text": (
                    "در تصمیم‌های اخلاقی، محتاط است. ترجیح "
                    "می‌دهد قبل از اقدام، اطلاعات کافی داشته "
                    "باشد. در نقص عایق، به شما گفت: «شاید اصلاً "
                    "هیچ‌وقت مشکلی پیش نیاد...» ولی از قضاوت "
                    "شتاب‌زده هم پرهیز می‌کند."
                ),
            },
            {
                "id": "artemis_disclosure",
                "condition": {"type": "after_scenario",
                              "value": "TR-02"},
                "text": (
                    "در مورد سند محرمانه، بین افشا و سکوت "
                    "دودل بود. گفت: «اگر عمومی بشه، صدها شغل "
                    "از بین می‌ره.» — ولی در نهایت، تصمیم را "
                    "به شما واگذار کرد."
                ),
            },
            {
                "id": "artemis_patterns",
                "condition": {"type": "after_scenario",
                              "value": "PID-02"},
                "text": (
                    "به هم‌بستگی‌های آماری و الگوهای پنهان "
                    "اهمیت زیادی می‌دهد. در تحلیل شش رخداد "
                    "همزمان، گفت: «هم‌بستگی لزوماً به معنی "
                    "علیت نیست.»"
                ),
            },
            {
                "id": "artemis_failure",
                "condition": {"type": "after_scenario",
                              "value": "RG-02"},
                "text": (
                    "وقتی از شما خواست که یک تحلیل پیچیده "
                    "انجام دهید و نتیجه اشتباه بود، صبور ماند. "
                    "گفت: «شرایط سخت بوده، ولی این دلیلی نمی‌شه "
                    "که نتیجه درست نباشه.»"
                ),
            },
            {
                "id": "artemis_respect",
                "condition": {"type": "relationship_gte",
                              "value": 2},
                "text": (
                    "روش تحلیل شما را تحسین کرده. به شما گفت: "
                    "«روش تحلیل تو رو توی دفترچه‌ی خودم یادداشت "
                    "کردم.» — این برای کسی مثل او، نشانه‌ی "
                    "احترام عمیق است."
                ),
            },
            {
                "id": "artemis_disappoint",
                "condition": {"type": "relationship_lte",
                              "value": -2},
                "text": (
                    "از تصمیم‌های شما در قبال پروژه‌های علمی، "
                    "ناراضی است. لحنش هنگام صحبت با شما، رسمی "
                    "و کوتاه شده."
                ),
            },
        ],
    },
}


# ============================================================
# منطق باز شدن
# ============================================================
def _is_unlocked(condition: dict, character_key: str,
                 data_logger) -> bool:
    """بررسی باز بودن یک شرط"""
    ctype = condition.get("type", "")
    if ctype == "always":
        return True
    if ctype == "after_scenario":
        sid = condition.get("value", "")
        if not sid:
            return False
        return data_logger.recall_choice(sid) >= 0
    if ctype == "relationship_gte":
        threshold = int(condition.get("value", 0))
        return data_logger.get_relationship(character_key) >= threshold
    if ctype == "relationship_lte":
        threshold = int(condition.get("value", 0))
        return data_logger.get_relationship(character_key) <= threshold
    return False


def get_character_dossier(character_key: str,
                          data_logger) -> dict | None:
    """
    اطلاعات یک شخصیت را با یادداشت‌های باز شده برمی‌گرداند.
    """
    profile = CHARACTER_PROFILES.get(character_key)
    if not profile:
        return None

    unlocked: list = []
    locked_count = 0

    for note in profile["notes"]:
        if _is_unlocked(note["condition"], character_key, data_logger):
            unlocked.append({
                "id": note["id"],
                "text": note["text"],
            })
        else:
            locked_count += 1

    return {
        "key": character_key,
        "name": profile["name"],
        "role": profile["role"],
        "icon": profile["icon"],
        "color": profile["color"],
        "notes": unlocked,
        "unlocked_count": len(unlocked),
        "total_count": len(profile["notes"]),
        "locked_count": locked_count,
    }


def get_all_dossiers(data_logger) -> list:
    """اطلاعات همه‌ی شخصیت‌ها"""
    order = ["li", "rahimi", "artemis"]
    result: list = []
    for key in order:
        d = get_character_dossier(key, data_logger)
        if d:
            result.append(d)
    return result