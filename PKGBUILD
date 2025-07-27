# Maintainer: Your Name <your@email.com>
# Replace 'Your Name' and 'your@email.com' with your actual name and email.
# Replace 'yourusername' and 'hel-space-fight' in url and source with your GitHub details.

pkgname=hel-space-fight
pkgver=1.0.0 # استخدم إصدارًا مناسبًا لمشروعك، وقم بتحديثه عند كل إصدار جديد.
pkgrel=1
pkgdesc="A space-themed game built with Pygame for the Helwan Linux community."
arch=('any')
url="https://github.com/helwan-linux/space-fight" # رابط مستودع GitHub الخاص بك
license=('MIT') # أو الترخيص الذي اخترته للمشروع
depends=('python' 'python-pygame') # المتطلبات الأساسية للعبة

# تم التعديل هنا ليتوافق مع اسم الملف الذي يتم تنزيله من GitHub لفرع main.
# GitHub عادةً ما يسمي ملف الأرشيف الخاص بالفرع 'main' بـ 'main.tar.gz'
source=("main.tar.gz::${url}/archive/refs/heads/main.tar.gz")

# SHA256SUMs: يجب أن يتم حسابها بعد تنزيل الملف المضغوط.
# يمكنك تركها 'SKIP' مؤقتًا، ثم قم بتشغيل 'makepkg -g' لحسابها تلقائيًا.
sha256sums=('SKIP')


build() {
    # المسار إلى مجلد المصدر المستخرج هو 'space-fight-main'
    cd "${srcdir}/space-fight-main"
}

package() {
    # هذا هو المكان الذي يتم فيه نسخ الملفات إلى مجلد الحزمة (pkgdir)

    # الانتقال إلى المجلد المستخرج للمشروع
    cd "${srcdir}/space-fight-main"
    # الانتقال إلى المجلد الفرعي الذي يحتوي على ملفات اللعبة الفعلية
    cd "hel-space-fight" # <--- هذا السطر تم إضافته

    # إنشاء المجلد الوجهة داخل الحزمة
    # من الأفضل وضع الألعاب في /usr/share/games/
    install -d "${pkgdir}/usr/share/games/${pkgname}/assets"
    install -d "${pkgdir}/usr/bin"
    install -d "${pkgdir}/usr/share/applications" # إضافة لملف سطح المكتب

    # نسخ ملفات اللعبة إلى مجلد `/usr/share/games/hel-space-fight/`
    cp -r ./assets/* "${pkgdir}/usr/share/games/${pkgname}/assets/"
    cp ./entities_pygame.py "${pkgdir}/usr/share/games/${pkgname}/"
    cp ./game_core_pygame.py "${pkgdir}/usr/share/games/${pkgname}/"
    cp ./game_data.json "${pkgdir}/usr/share/games/${pkgname}/"
    cp ./main.py "${pkgdir}/usr/share/games/${pkgname}/"
    cp ./main_pygame.py "${pkgdir}/usr/share/games/${pkgname}/"
    cp ./screens_pygame.py "${pkgdir}/usr/share/games/${pkgname}/"
    cp ./utils.py "${pkgdir}/usr/share/games/${pkgname}/"

    # إنشاء ملف تشغيلي (wrapper script) في /usr/bin لتشغيل اللعبة بسهولة
    # هذا يسمح للمستخدم بتشغيل 'hel-space-fight' مباشرة من الطرفية

    # التعديل الحاسم هنا هو إضافة 'cd "$GAME_DIR" || exit 1'
    # لضمان أن المسار الحالي للسكريبت يتغير إلى مجلد اللعبة
    # قبل تشغيلها، مما يحل مشاكل المسارات النسبية للأصول (الصور والأصوات).
    cat <<EOF > "${pkgdir}/usr/bin/${pkgname}"
#!/bin/bash
GAME_DIR="/usr/share/games/${pkgname}"
# الانتقال إلى مجلد اللعبة لضمان أن المسارات النسبية للأصول تعمل
cd "\$GAME_DIR" || exit 1
# تعيين PYTHONPATH لضمان العثور على الوحدات النمطية (modules)
export PYTHONPATH="\$GAME_DIR:\$PYTHONPATH"
python3 "main_pygame.py" "\$@"
EOF
    chmod +x "${pkgdir}/usr/bin/${pkgname}"

    # ملف سطح المكتب
    cat <<EOF > "${pkgdir}/usr/share/applications/$pkgname.desktop"
[Desktop Entry]
Name=Hel Space Fight
Comment=2D space shooter game built with Pygame
Exec=$pkgname
Icon=/usr/share/$pkgname/assets/icon.png
Terminal=false
Type=Application
Categories=Game;ActionGame;
EOF

    # تنظيف: إزالة أي ملفات غير ضرورية من الحزمة النهائية
    # (مثل .git، ملفات PKGBUILD، cache files)
    find "${pkgdir}/usr/share/games/${pkgname}" -name "__pycache__" -exec rm -rf {} +
    rm -f "${pkgdir}/usr/share/games/${pkgname}/PKGBUILD"
    # يمكنك إضافة المزيد من أوامر rm -f / rm -rf لأي ملفات مؤقتة أو غير ضرورية
}
