# Maintainer: Saeed Badrelden <you@example.com>
pkgname=hel-space-fight
pkgver=1.0.0
pkgrel=1
pkgdesc="A 2D space shooter game built with pygame"
arch=('any')
url="https://github.com/helwan-linux/space-fight"
license=('MIT')
depends=('python' 'python-pygame')
makedepends=('unzip')
source=("$pkgname-$pkgver.zip::$url/archive/refs/heads/main.zip")
sha256sums=('SKIP')

build() {
  echo "Nothing to build"
}

package() {
  cd "$srcdir/space-fight-main"

  # انسخ ملفات اللعبة
  install -d "$pkgdir/usr/share/$pkgname"
  cp -r . "$pkgdir/usr/share/$pkgname"

  # سكربت التشغيل
  install -d "$pkgdir/usr/bin"
  echo -e "#!/bin/bash\npython /usr/share/$pkgname/main_pygame.py" > "$pkgdir/usr/bin/$pkgname"
  chmod +x "$pkgdir/usr/bin/$pkgname"

  # ملف سطح المكتب
  install -d "$pkgdir/usr/share/applications"
  cat > "$pkgdir/usr/share/applications/$pkgname.desktop" <<EOF
[Desktop Entry]
Name=Hel Space Fight
Comment=2D space shooter game built with Pygame
Exec=$pkgname
Icon=/usr/share/$pkgname/assets/icon.png
Terminal=false
Type=Application
Categories=Game;ActionGame;
EOF
}

