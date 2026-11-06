# حالة المشروع — 2026-11-06

الريبو: `ahralf81m/opencv` (fork ديال OpenCV)
البرانش ديال الخدمة: `ccr-7add2bc2-qq3lk8`

> هاد الوثيقة هي صورة واقعية للمشروع فهاد اللحظة. تعمرات من محتوى الريبو ومن جوج تحققات درتهم فـ
> conteneur Linux: configuration ديال CMake وcompilation جزئية. أي حاجة ما تحققتش منها كتبتها
> بوضوح بلي ما تجرباتش.

## 1. الخلاصة

- الريبو هو fork ديال OpenCV **ما تبدل فيه والو**. `master` و`origin/master` والبرانش ديال الخدمة
  كلهم واقفين على نفس الـ commit (`ca8c3dd9`)، وما كاين حتى commit ديال الـ fork.
- الكود **واقف فـ 2021-03-22**، يعني تقريباً 5 سنين و7 شهور قبل تاريخ هاد التقرير. النسخة المصرحة
  هي **4.5.2-pre**، يعني قبل ما تخرج release 4.5.2.
- ما كاينش ربط مع الريبو الأصلي: `origin` هو الـ remote الوحيد، وما كاينش remote سميتو `upstream`.
- الموديلات `core` و`imgproc` **كيدوزو configuration وcompilation** مزيان بـ toolchain ديال دابا
  (شوف §5). الموديلات الأخرين ما تجرباوش.

## 2. بطاقة الريبو

| العنصر | القيمة |
|---|---|
| النسخة (`version.hpp`) | 4.5.2، الحالة `-pre` |
| آخر commit | `ca8c3dd9` — « Merge remote-tracking branch 'upstream/3.4' into merge-3.4 » |
| تاريخ آخر commit | 2021-03-22 (Alexander Alekhin) |
| التاريخ (historique) | 1 400 commit |
| الفيشيات المتتبعة | 6 759 |
| الحجم | `.git` ≈ 93 Mo، نسخة الخدمة ≈ 195 Mo |
| البرانشات | `master`، `ccr-7add2bc2-qq3lk8` (محلية وبعيدة) |
| commits قدام `master` | 0 (قبل ما نزيدو هاد الفيشي) |
| Tags | ما كاين حتى واحد |
| الرخصة | `LICENSE` و`COPYRIGHT` كاينين فـ الجذر |

## 3. شنو كاين فـ الريبو

### 3.1 الموديلات (`modules/`)

21 ديال الدوسيات ديال الموديلات. عدد الفيشيات المتتبعة فكل موديل (sources وheaders / tests / tests
ديال الأداء):

| Module | Src + include | Tests | Perf |
|---|---:|---:|---:|
| core | 315 | 43 | 33 |
| dnn | 312 | 25 | 9 |
| highgui | 280 | 3 | 0 |
| gapi | 207 | 98 | 24 |
| imgproc | 147 | 56 | 40 |
| videoio | 74 | 9 | 5 |
| calib3d | 65 | 35 | 8 |
| imgcodecs | 53 | 11 | 2 |
| features2d | 47 | 26 | 7 |
| video | 41 | 16 | 16 |
| flann | 40 | 3 | 0 |
| stitching | 32 | 10 | 7 |
| photo | 29 | 11 | 5 |
| ml | 20 | 14 | 0 |
| ts | 20 | 0 | 0 |
| objdetect | 13 | 5 | 5 |
| js | 5 | 13 | 36 |
| world | 3 | 0 | 0 |
| java, objc, python | 0 | 20 / 3 / 29 | 0 |

ملاحظات:
- `highgui` و`flann` و`ml` عندهم tests قليلين بزاف بالنسبة لحجم الكود ديالهم.
- `dnn` فيه 25 فيشي ديال test مقابل 312 فيشي ديال sources.
- `java` و`objc` و`python` هوما موديلات ديال bindings: ما كاين حتى فيشي متتبع تحت `src/` ولا
  `include/` (الكود ديالهم كاين فبلاصة أخرى فنفس الموديل)، وهنا غير الـ tests ديالهم اللي تحسبو.

### 3.2 دوسيات أخرى

- `3rdparty/`: 20 دوسي، منهم `ffmpeg`، `ippicv`، `libjpeg-turbo`، `libpng`، `libtiff`، `libwebp`،
  `openexr`، `openjpeg`، `protobuf`، `tbb`، `zlib`.
- `samples/`: أمثلة C++ (234 فيشي)، Python (135)، `data` (113)، WinRT (110)، WP8 (102)،
  Android (100)، Java (87)، `dnn` (70)، Swift (65).
- `doc/`، `apps/`، `cmake/`، `platforms/`، `include/`، `data/` (39 فيشي متتبع).

### 3.3 اللغات (الفيشيات المتتبعة حسب الامتداد)

C++: 1 524 `.cpp`، 755 `.hpp`. C: 366 `.c`، 716 `.h`. Python: 306. Java: 199. OpenCL: 109 `.cl`.
CMake: 140. التوثيق: 287 `.markdown`.

## 4. النشاط

- الـ commits اللي تاريخ الـ commit ديالهم من بعد 2021-01-01، تواريخ المؤلفين ديالهم كتمشي من
  2020-12-08 حتى 2021-03-22.
- 97 commit من 2021-03-01، منهم 63 ديال نفس المؤلف (Alexander Alekhin). هاد النشاط جاي من الريبو
  الأصلي، ماشي من الـ fork.
- ما كاين حتى نشاط ديال الـ fork: ما كاين commit محلي، ولا برانش ديال feature، ولا tag.
- نوع آخر التغييرات: fusions ديال pull requests جايين من الريبو الأصلي (منهم #19757، دعم
  `setLogLevel()` / `getLogLevel()` فـ JavaScript، و#19632، target ARM للـ inference).

## 5. التحققات اللي درتهم

البيئة: Linux، CMake 3.28.3، Ninja، GCC / G++ 13.3.0، Python 3 موجود، 4 ديال الـ cores.

| التحقق | النتيجة |
|---|---|
| Configuration ديال CMake (`core` و`imgproc` بوحدهم، بلا tests، بلا IPP ولا OpenCL ولا Java ولا Python) | نجحات فـ 23,6 ثانية |
| Compilation ديال `core` + `imgproc` (224 خطوة Ninja، `-j4`) | نجحات فـ 1 د و54 ث، 0 ديال الـ warnings اللي لقيت |
| Compilation ديال الموديلات الأخرين (`dnn`، `gapi`، `videoio`، `highgui`، إلخ) | **ما تجرباتش** |
| Compilation ديال الـ tests وtests ديال الأداء | **ما تجرباتش** |
| تشغيل الـ tests | **ما تجرباوش** |
| Bindings ديال Python وJava | **ما تجرباوش** |
| الخيارات الاختيارية (IPP، OpenCL، CUDA، FFmpeg ديال النظام، GUI) | **ما تجرباوش** |

قراءة بحذر: قاعدة كود ديال 2021 دازت compilation بـ GCC 13 فجوج موديلات، هادشي زوين، ولكن ما كيقول والو
على الموديلات اللي كتتأثر بزاف بتبدل الـ compilateurs والمكتبات (خصوصاً `dnn` و`gapi` والـ bindings).

## 6. الـ CI (Intégration continue)

كاين غير workflow واحد ديال GitHub Actions: `.github/workflows/arm64-build-checks.yml`.
- كيتشغل غير يدوياً (`workflow_dispatch`).
- الـ runner هو `ubuntu-18.04`، وهاد الصورة GitHub حيدها. يعني الـ workflow ما بقاش يقدر يتشغل
  بحالتو.
- كيستهدف Python 2.7 وPython 3.6، وكيدير clone ديال `opencv_contrib` بـ `--depth 1`، يعني ما
  كيثبتوش على نسخة متوافقة مع هاد الريبو.

ما كاين حتى CI أوتوماتيكي (عند push ولا pull request) خدام فهاد الـ fork.

## 7. المخاطر وحاجات خاص الانتباه ليها

1. **عمر الكود.** أزيد من خمس سنين ديال الإصلاحات، خصوصاً ديال الأمان، وديال تحديث الـ
   dependencies والتوافق مع compilateurs وأنظمة جداد، ماكايناش هنا. شوف `SECURITY.md` والإعلانات
   اللي كينشر الريبو الأصلي قبل ما تستعملو فـ production.
2. **Dependencies مدمجة وواقفة.** المكتبات اللي فـ `3rdparty/` (الصور، zlib، protobuf 3.5.1،
   FFmpeg، إلخ) هي ديال مارس 2021. خاصك تعتابرها يمكن فيها ثغرات حتى يتدار ليها audit.
3. **ما كاينش ربط مع الريبو الأصلي.** بلا remote `upstream`، ما كاين تحديث ممكن بلا ما تعدل
   الـ configuration قبل.
4. **الـ CI ما خدامش** (§6): ما كاين حتى حاجة كتكشف regression دابا.
5. **محتوى `opencv_contrib` ماشي هنا.** الريبو فيه غير النواة؛ كلشي اللي جاي من `opencv_contrib`
   خاصك تجيبو بوحدو، بنسخة متوافقة.
6. **الهدف ديال الـ fork ما موثقش.** الـ `README.md` هو ديال الريبو الأصلي وما كاين حتى فيشي كيقول
   علاش هاد الـ fork كاين ولا شنو متوقع منو.

## 8. القرارات اللي خاصها تتاخد

| السؤال | الخيارات |
|---|---|
| شنو هو الهدف ديال الـ fork؟ | نخدمو انطلاقاً من هاد الـ snapshot، ولا نبداو من نسخة جديدة من الريبو الأصلي |
| واش خاص نلحقو الريبو الأصلي؟ | نزيدو remote `upstream`، ومن بعد نديرو merge ولا rebase لـ release جديدة |
| شنو هو نطاق الـ build؟ | نحددو لائحة الموديلات والخيارات اللي كتستعمل بصح، ومن بعد نتحققو منهم كاملين |
| أي CI؟ | نبدلو workflow ARM64 القديم بـ workflow Linux على runner حالي |

## 9. الخطوات اللي كنقترح

1. نأكدو الهدف ديال الـ fork ونزيدوه فـ `README.md`.
2. نزيدو remote `upstream` (`https://github.com/opencv/opencv`) ونقيسو الفرق مع الريبو الأصلي.
3. نديرو compilation للموديلات المستهدفة كاملين ونشغلو الـ tests الأساسية (`opencv_test_core`،
   `opencv_test_imgproc`)، ونكتبو النتائج هنا.
4. نرجعو CI بسيط (configuration وcompilation على runner مدعوم).
5. نديرو audit ولا نحدثو الـ dependencies ديال `3rdparty/` حسب حاجة المشروع.

## 10. حدود هاد التقرير

- الريبو ما فيهش سجل ديال القرارات، ولا tickets، ولا roadmap: الهدف ديال الـ fork وفين وصل ما
  كيبانوش، وهاد التقرير معتمد غير على الكود وعلى historique ديال git.
- الفرق الحقيقي مع الريبو الأصلي دابا ما تقاسش: الـ conteneur ما كانش فيه remote `upstream`
  مضبوط.
- الأرقام ديال §3 هي عدد الفيشيات المتتبعة من طرف git (`git ls-files`)، ماشي عدد السطور ديال الكود.
