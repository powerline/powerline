# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/dev-python/setuptools/setuptools-9999.ebuild,v 1.1 2013/01/11 09:59:31 mgorny Exp $

EAPI="5"
PYTHON_COMPAT=( python2_7 )

#if LIVE
EGIT_REPO_URI="https://github.com/Lokaltog/${PN}"
EGIT_BRANCH="develop"
inherit git
#endif

inherit distutils-r1 eutils font
DESCRIPTION="The ultimate statusline/prompt utility."
HOMEPAGE="http://github.com/Lokaltog/powerline"
SRC_URI=""

LICENSE="CC-Attribution-ShareAlike-3.0"
SLOT="0"
KEYWORDS="~alpha ~amd64 arm ~hppa ~ia64 ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86 ~ppc-aix ~amd64-fbsd ~sparc-fbsd ~x86-fbsd ~x64-freebsd ~x86-freebsd ~hppa-hpux ~ia64-hpux ~x86-interix ~amd64-linux ~ia64-linux ~x86-linux ~ppc-macos ~x64-macos ~x86-macos ~m68k-mint ~sparc-solaris ~sparc64-solaris ~x64-solaris ~x86-solaris"
IUSE="vim doc"

#if LIVE
SRC_URI=
KEYWORDS=
#endif

S="${WORKDIR}/${PN}"

RDEPEND="vim? ( || ( app-editors/vim[python] app-editors/gvim[python] ) )"
DEPEND="doc? ( dev-python/sphinx dev-python/docutils )"

FONT_SUFFIX="otf"
FONT_S="${S}/font"

FONT_CONF=(
	"${FONT_S}/10-powerline-symbols.conf"
)

src_compile() {
	distutils-r1_src_compile
	if use doc ; then
		einfo "Generating documentation"
		sphinx-build -b html docs/source docs_output
	fi
}

src_install() {
	unset DOCS
	font_src_install
	distutils-r1_src_install
	use doc && dohtml -r docs_output/*
}
