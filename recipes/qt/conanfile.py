from conans import ConanFile, tools
from conan.tools.files import collect_libs, copy, rmdir
from conan.tools.microsoft import msvc_runtime_flag, is_msvc
from conan.tools.build import build_jobs
import os


class QtConan(ConanFile):
    name = "qt"
    version = "5.15.3"
    url = "https://github.com/JaySinco/dev-setup"
    homepage = "https://download.qt.io/official_releases/qt/"
    description = "Qt is a cross-platform framework for graphical user interfaces"
    license = "LGPL-3.0"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def layout(self):
        build_folder = "out"
        build_type = str(self.settings.build_type)
        self.folders.source = "src"
        self.folders.build = os.path.join(build_folder, build_type)

    def source(self):
        self._get_source("qtbase")
        self._get_source("qttools")

    def package_id(self):
        del self.info.settings.build_type

    def package(self):
        self._configure("qtbase")
        self._build_and_install("qtbase")
        self._run_qmake("qttools")
        self._build_and_install("qttools")

        tools.remove_files_by_mask(os.path.join(
            self.package_folder, "lib"), "*.pdb*")
        tools.remove_files_by_mask(os.path.join(
            self.package_folder, "bin"), "*.pdb")

        copy(self, "LICENSE*",
             dst=os.path.join(self.package_folder, "licenses"),
             src=os.path.join(self.source_folder, "qtbase"))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")

    def _configure(self, name):
        config_cmd = "{} {}".format(self._configure_exe, self._config_flags)
        self.run(command=config_cmd,
                 cwd=os.path.join(self.source_folder, name))

    def _build_and_install(self, name):
        build_cmd = "{} {}".format(self._make_exe, self._build_flags)
        self.run(command=build_cmd,
                 cwd=os.path.join(self.source_folder, name))

        install_cmd = "{} install".format(self._make_exe)
        self.run(command=install_cmd,
                 cwd=os.path.join(self.source_folder, name))

    def _run_qmake(self, name):
        qmake_cmd = os.path.join(self.package_folder, "bin", "qmake")
        self.run(command=qmake_cmd,
                 cwd=os.path.join(self.source_folder, name))

    def _get_source(self, name):
        srcFile = os.path.join(
            tools.get_env("JAYSINCO_SOURCE_REPO"),
            "{}-everywhere-opensource-src-{}.tar.xz".format(name, self.version))
        tools.unzip(srcFile, destination=os.path.join(
            self.source_folder, name), strip_root=True)

    @property
    def _configure_exe(self):
        return "configure.bat" if tools.os_info.is_windows else "configure"

    @property
    def _config_flags(self):
        flags = []
        flags.append("--prefix={}".format(self.package_folder))
        flags.append("--nomake=examples")
        flags.append("--nomake=tests")
        flags.append("-confirm-license")
        flags.append("-opensource")
        if not self.options.shared:
            flags.append("-static")
            if is_msvc(self) and "MT" in msvc_runtime_flag(self):
                flags.append("-static-runtime")
        else:
            flags.append(0, "-shared")
        if self.settings.build_type == "Debug":
            flags.append("-debug")
        else:
            flags.append("-release")
        flags.append("--opengl=desktop")
        flags.append("--c++std=c++17")
        return " ".join(flags)

    @property
    def _make_exe(self):
        return "jom" if tools.os_info.is_windows else "make"

    @property
    def _build_flags(self):
        flags = []
        flags.append(f"-j{build_jobs(self)}")
        return " ".join(flags)