# luajit is not available for some architectures and not at all on RHEL7
%if 0%{?rhel} <= 7
%bcond_with lua
%else
%ifarch ppc64 ppc64le s390x
%bcond_with lua
%else
%bcond_without lua
%endif
%endif

Name:           bcc
Version:        0.6.1
Release:        2%{?dist}
Summary:        BPF Compiler Collection (BCC)
License:        ASL 2.0
URL:            https://github.com/iovisor/bcc
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
Patch0:         link-against-libLLVM.so-instead-of-static-libs.patch
Patch1:         Fix-tools-for-RHEL-7.patch
Patch2:         sslsniff-add-NSS-support-1908.patch
Patch3:         llcstat-print-a-nicer-error-message-when-hardware-ev.patch
Patch4:         Miscellaneous-fixes-1914.patch
# tests/cc doesn't compile on s390x, so disable it until we have a better fix
Patch10:         Disable-tests-cc.patch

# Arches will be included as upstream support is added and dependencies are
# satisfied in the respective arches
ExcludeArch: i686 ppc s390

BuildRequires:  bison, cmake >= 2.8.7, flex, libxml2-devel
BuildRequires:  python-devel
BuildRequires:  elfutils-libelf-devel
BuildRequires:  ncurses-devel
%if %{with lua}
BuildRequires: pkgconfig(luajit)
%endif
BuildRequires: llvm-private-devel >= 6.0.1-0.3

Requires:       %{name}-tools = %{version}-%{release}
Requires:       llvm-private >= 6.0.1-0.3

%description
BCC is a toolkit for creating efficient kernel tracing and manipulation
programs, and includes several useful tools and examples. It makes use of
extended BPF (Berkeley Packet Filters), formally known as eBPF, a new feature
that was first added to Linux 3.15. BCC makes BPF programs easier to write,
with kernel instrumentation in C (and includes a C wrapper around LLVM), and
front-ends in Python and lua. It is suited for many tasks, including
performance analysis and network traffic control.


%package devel
Summary:        Shared library for BPF Compiler Collection (BCC)
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
The %{name}-devel package contains libraries and header files for developing
application that use BPF Compiler Collection (BCC).


%package doc
Summary:        Examples for BPF Compiler Collection (BCC)
BuildArch:      noarch

%description doc
Examples for BPF Compiler Collection (BCC)


%package -n python-%{name}
Summary:        Python bindings for BPF Compiler Collection (BCC)
Requires:       %{name}%{?_isa} = %{version}-%{release}
%{?python_provide:%python_provide python-%{srcname}}

%description -n python-%{name}
Python bindings for BPF Compiler Collection (BCC)


%if %{with lua}
%package lua
Summary:        Standalone tool to run BCC tracers written in Lua
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description lua
Standalone tool to run BCC tracers written in Lua
%endif


%package tools
Summary:        Command line tools for BPF Compiler Collection (BCC)
Requires:       python-%{name} = %{version}-%{release}
Requires:       python-netaddr
Requires:       kernel-devel

%description tools
Command line tools for BPF Compiler Collection (BCC)

%prep
%setup
%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1

%ifarch s390x
%patch10 -p1
%endif

%build
%cmake . \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo\
        -DCMAKE_CXX_FLAGS='-std=c++11 -I/usr/include/llvm-private/'\
        -DREVISION_LAST=%{version} -DREVISION=%{version}\
        -DCMAKE_LIBRARY_PATH=/usr/lib64/clang-private/\
	-DCMAKE_INSTALL_RPATH=/usr/lib64/clang-private/
%make_build

%install
%make_install

# Move man pages to the right location
mkdir -p %{buildroot}%{_mandir}
mv %{buildroot}%{_datadir}/%{name}/man/* %{buildroot}%{_mandir}/
# Avoid conflict with other manpages
# https://bugzilla.redhat.com/show_bug.cgi?id=1517408
for i in `find %{buildroot}%{_mandir} -name "*.gz"`; do
  tname=$(basename $i)
  rename $tname %{name}-$tname $i
done
# Fix the symlink too
for i in `find %{buildroot}%{_mandir} -lname \*.gz` ; do
    target=`readlink $i`;
    ln -sf bcc-$target $i;
done
mkdir -p %{buildroot}%{_docdir}/%{name}
mv %{buildroot}%{_datadir}/%{name}/examples %{buildroot}%{_docdir}/%{name}/

# We cannot run the test suit since it requires root and it makes changes to
# the machine (e.g, IP address)
#%check

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%files
%doc README.md
%license LICENSE.txt
%{_libdir}/lib%{name}.so.*
%{_libdir}/libbpf.so.*

%files devel
%{_libdir}/lib%{name}.so
%{_libdir}/libbpf.so
%{_libdir}/pkgconfig/lib%{name}.pc
%{_includedir}/%{name}/

%files -n python-%{name}
%{python_sitelib}/%{name}*

%files doc
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/examples/

%files tools
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/tools
%dir %{_datadir}/%{name}/introspection
%{_datadir}/%{name}/tools/*
%{_datadir}/%{name}/introspection/*
%exclude %{_datadir}/%{name}/tools/old/
# inject relies on BPF_KPROBE_OVERRIDE which is absent on RHEL 7
%exclude %{_datadir}/%{name}/tools/inject
# ZFS isn't available on RHEL
%exclude %{_datadir}/%{name}/tools/zfs*
%{_mandir}/man8/*

%if %{with lua}
%files lua
%{_bindir}/bcc-lua
%endif


%changelog
* Fri Sep 21 2018 Jerome Marchand <jmarchan@redhat.com> - 0.6.1-2
- Set a minimal version for llvm-private(-devel)

* Thu Aug 16 2018 Jerome Marchand <jmarchan@redhat.com> - 0.6.1-1
- Rebase on v0.6.1
- Fix tcpsubnet
- Reinstate llcstat tool
- Remove inject tool
- Add NSS support to sslsniff
- Fixes miscellaneous error uncovered by covscan

* Wed Jul 04 2018 Jerome Marchand <jmarchan@redhat.com> - 0.6.0-3
- Fix tools on RHEL 7
- Remove llcstat and ZFS tools.

* Tue Jun 26 2018 Jerome Marchand <jmarchan@redhat.com> - 0.6.0-2
- Add llvm-private requirement
- Fix manpages symlinks

* Tue Jun 19 2018 Jerome Marchand <jmarchan@redhat.com> - 0.6.0-1
- Rebase on bcc-0.6.0

* Thu Jun 07 2018 Jerome Marchand <jmarchan@redhat.com> - 0.5.0-6
- Enables build on RHEL 7

* Thu May 24 2018 Jerome Marchand <jmarchan@redhat.com> - 0.5.0-5
- Enables build on ppc64(le) and s390x arches

* Thu Apr 05 2018 Rafael Santos <rdossant@redhat.com> - 0.5.0-4
- Resolves #1555627 - fix compilation error with latest llvm/clang

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Feb 02 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.5.0-2
- Switch to %%ldconfig_scriptlets

* Wed Jan 03 2018 Rafael Santos <rdossant@redhat.com> - 0.5.0-1
- Rebase to new released version

* Thu Nov 16 2017 Rafael Santos <rdossant@redhat.com> - 0.4.0-4
- Resolves #1517408 - avoid conflict with other manpages

* Thu Nov 02 2017 Rafael Santos <rdossant@redhat.com> - 0.4.0-3
- Use weak deps to not require lua subpkg on ppc64(le)

* Wed Nov 01 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.4.0-2
- Rebuild for LLVM5

* Wed Nov 01 2017 Rafael Fonseca <rdossant@redhat.com> - 0.4.0-1
- Resolves #1460482 - rebase to new release
- Resolves #1505506 - add support for LLVM 5.0
- Resolves #1460482 - BPF module compilation issue
- Partially address #1479990 - location of man pages
- Enable ppc64(le) support without lua
- Soname versioning for libbpf by ignatenkobrain

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.3.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.3.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Mar 30 2017 Igor Gnatenko <ignatenko@redhat.com> - 0.3.0-2
- Rebuild for LLVM4
- Trivial fixes in spec

* Fri Mar 10 2017 Rafael Fonseca <rdossant@redhat.com> - 0.3.0-1
- Rebase to new release.

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.2.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Jan 10 2017 Rafael Fonseca <rdossant@redhat.com> - 0.2.0-2
- Fix typo

* Tue Nov 29 2016 Rafael Fonseca <rdossant@redhat.com> - 0.2.0-1
- Initial import
