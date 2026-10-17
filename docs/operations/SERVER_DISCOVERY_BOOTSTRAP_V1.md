# تشغيل اكتشاف الخوادم وبداية دورة الهندسة الذاتية — v1

**التاريخ:** 2026-10-09  
**السلطة الكانونية:** VAIXLNS  
**الحالة:** أداة اكتشاف محدودة + سجل مصادر؛ لا تمثل نشرًا إنتاجيًا ولا تثبت تشغيل أي خادم.

## لماذا تبدأ الهندسة من الخوادم؟

لا تبدأ «الهندسة المجنونة» بإطلاق وكلاء بلا حدود؛ تبدأ بتحويل كل خدمة إلى مورد له هوية وعقد ونطاق وأدلة. عندها تستطيع المنظومة أن تعرف ما الذي يعمل، وما الذي فشل، وما الذي يمكن إصلاحه بأمان، وما الذي يجب إبقاؤه في الحجر.

## ما كشفه فحص المصادر الحالية

1. يعرّف ملف `deploy/federation/federation.yaml` طبقة تشغيل مطلوبة تضم ingress وAPI gateway وevent bus وPostgres ومدير أسرار ومقاييس وسجلات؛ Redis اختياري والتتبعات موصى بها. **التعريف في الملف ليس دليلًا على أن هذه الخدمات منشورة أو متصلة**.
2. أرشيف المشروع يصف خدمة HTTP داخل شبكة خاصة. وضعت مرجعها في السجل عبر `VAIXLNS_DISCOVERY_TARGET` فقط؛ عنوانها الحرفي غير منشور هنا، ويجب فحصها من جهاز على الشبكة المصرح بها.
3. توثق Ollama واجهة محلية افتراضية على `127.0.0.1:11434`. حالة تثبيتها أو تشغيلها على أي جهاز تابع للمشروع غير معروفة إلى أن يُنفذ الفحص المحلي.
4. يذكر README في `vaixlns-core` واجهة `http://localhost:8000/health`، بينما سجل حالة التشغيل الكانوني يشير إلى أن مصدرًا تنفيذيًا قابلًا للتشغيل لم يُثبت في الشجرة التي راجعها. لذلك أبقيت الهدف معطلًا افتراضيًا حتى تُحل هذه المفارقة.
5. مستودع NEXENT هو سطح اكتشاف/بحث؛ لم يُعثر في الأدلة المفحوصة على عنوان نشر إنتاجي له. ومستودع تدفقات n8n ليس برهانًا على وجود نسخة n8n متصلة بحساباتك.
6. GitHub Actions طبقة تحقق CI وليست خادم تطبيق دائمًا. لا تمنحنا نتيجة CI عنوان API حيًا أو إثبات تشغيل إنتاجي.

## ما أُضيف في هذه الحزمة

- `registry/infrastructure/SERVER_DISCOVERY_REGISTRY_V1.json`: يفرّق بين هدف موثق بالأرشيف، وخدمة محلية مرشحة، وادعاء في README، ومتطلبات بنية تحتية غير مربوطة.
- `tools/server_discovery_probe.py`: فاحص Python مستقل بمكتبات قياسية فقط؛ ينفذ GET واحدًا محددًا لكل هدف مسموح، بمهلة لا تتجاوز 5 ثوانٍ، ويوقف التحويلات، ولا يفحص نطاقات الشبكة، ولا يحفظ أجسام الاستجابات.
- `tests/test_server_discovery_probe.py`: اختبارات لنطاق الشبكة، ورفض URL يحوي بيانات اعتماد/استعلامًا، وحدّ المهلة، وتنقيح عنوان الشبكة الخاصة.
- لا يعيد هذا الإصدار تشغيل خدمة أو يغيّر إعداداتها تلقائيًا. الإصلاح الذاتي يأتي بعد إثبات هوية الخدمة وعقدها وحدود صلاحياتها.

## كيف تشغّل الفحص

من نسخة محلية موثوقة من المستودع، على الجهاز الذي تريد فحصه:

```bash
python tools/server_discovery_probe.py
```

سيختبر ذلك هدف Ollama المحلي المرشح فقط؛ إذا لم تكن الخدمة تستمع فستُسجّل النتيجة كفشل وصول، لا كفشل في Ollama نفسه ولا كدليل على أن البرنامج غير مثبت.

لفحص عنوان الشبكة الخاصة الذي تملكه أو لديك تصريح باختباره، استخدم عنوانه الفعلي من شبكتك، ولا تضعه في مستودع عام:

**PowerShell على Windows**
```powershell
$env:VAIXLNS_DISCOVERY_TARGET = "http://<PRIVATE-IP>:<PORT>/<KNOWN-PATH>"
python tools/server_discovery_probe.py --allow-configured-lan-target --output artifacts/server-discovery/probe.json
```

**Bash**
```bash
export VAIXLNS_DISCOVERY_TARGET="http://<PRIVATE-IP>:<PORT>/<KNOWN-PATH>"
python tools/server_discovery_probe.py --allow-configured-lan-target --output artifacts/server-discovery/probe.json
```

استبدل القيم بين الأقواس بعنوان حرفي خاص داخل الشبكة ومسار معروف لديك. يقبل الفاحص عنوان IP حرفيًا من النطاق الخاص فقط عند تفعيل الخيار الصريح؛ لا يقبل اسم نطاق عامًا لهذه العملية، ولا يتبع التحويلات إلى وجهات أخرى. احتفظ بملف الأدلة محليًا قبل مشاركة النتائج. لا ترفق رموز الوصول أو رؤوس المصادقة أو بيانات الاستجابة الخام.

لتشغيل الاختبارات محليًا:

```bash
python -m unittest discover -s tests -p "test_server_discovery_probe.py" -v
```

## كيف يبدأ التشغيل الذاتي المضبوط؟

```text
ARCHIVE / REPOSITORY DISCOVERY
        ↓
SERVER ID + CONTRACT + OWNER
        ↓
QUARANTINE (unknown / drifted / expired)
        ↓
BOUNDED HEALTH + FUNCTIONAL TEST
        ↓
SANDBOX + CONTROLLED FAULT INJECTION
        ↓
FAILURE CLASSIFICATION + RECOVERY PLAN
        ↓
REPLAY + INDEPENDENT VERIFICATION
        ↓
FRESH EVIDENCE + CAUSAL IMPACT BUDGET
        ↓
EXPLICIT AUTHORITY + ADMISSION GATE
        ↓
CANARY EXECUTION + OBSERVABILITY
        ↓
CONTINUOUS REVALIDATION
```

### بوابات لا يجوز تجاوزها

- الاكتشاف للوجهات المحددة صراحةً فقط؛ لا مسح تلقائيًا للشبكة أو منافذها.
- فشل الصحة لا يمنح النظام صلاحية إعادة التشغيل أو النشر تلقائيًا.
- تقتصر المحاولة الأولى على GET، مع حد زمني وحجم استجابة محدودين، ولا تُتبع تحويلات HTTP.
- لا تُرسل أسرار داخل URL ولا تُكتب في السجلات. تبقى عناوين الشبكة الخاصة والإعدادات الحساسة خارج المستودع العام.
- قبل أي إصلاح آلي: إثبات هوية الخدمة، نسخة المصدر، العقد والاعتماديات، صلاحية التنفيذ، وحد أقصى للتغييرات والتكلفة ومدة التشغيل.
- أي تغيير إنتاجي يمر من sandbox إلى الاختبار ثم الموافقة المحددة والـcanary؛ لا يسمح للوكيل بمنح نفسه صلاحية أو اعتماد حالته بنفسه.
- يلزم لكل تشغيل سجل زمني، ونتيجة صحة، وهاش للاستجابة المحدودة، ونسخة المصدر، ونتيجة الاختبار، وقرار القبول. الاستجابة HTTP الناجحة دليل وصول فقط، وليست برهانًا على صحة الوظيفة.

## تعريف النجاح

يُصنّف الهدف `OBSERVED_REACHABLE` إذا استجاب بنجاح لطلب الفحص فقط. ولا يصبح `VERIFIED_SERVICE` إلا بعد مطابقة الهوية والعقد، واجتياز اختبار وظيفي مستقل، والتحقق من الصلاحيات، وإرفاق أدلة حديثة قابلة لإعادة الفحص. أما `PRODUCTION_READY` فيتطلب نشرًا معروفًا ومراقبة واستعادة مُختبرتين؛ لا ينتج أي من هذه الحالات من README أو فحص شبكة منفرد.

## المراجع الرسمية

- [Ollama API introduction](https://docs.ollama.com/api/introduction)
- [Ollama FAQ — default loopback binding](https://docs.ollama.com/faq)
- [GitHub Actions self-hosted runner security guidance](https://docs.github.com/en/actions/reference/security/secure-use)
- [Cloudflare Tunnel documentation](https://developers.cloudflare.com/tunnel/)
- [Temporal self-hosted service guide](https://docs.temporal.io/self-hosted-guide)

**مهم:** هذه الحزمة تبدأ جرد الخوادم واكتشافها بأمان؛ لا تدعي أنها اتصلت بخادمك الخاص من داخل المحادثة، ولا أنها شغلت منظومة VAIXLNS إنتاجيًا.
