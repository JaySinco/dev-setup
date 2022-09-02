from conans import ConanFile, tools
from conan.tools.files import collect_libs, copy, rmdir
from conan.tools.microsoft import msvc_runtime_flag
from conan.tools.build import build_jobs
import os


class BoostConan(ConanFile):
    name = "boost"
    version = "1.79.0"
    url = "https://github.com/JaySinco/conan"
    homepage = "https://www.boost.org"
    description = "Boost provides free peer-reviewed portable C++ source libraries"
    license = "BSL-1.0"

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
        self.folders.source = "src"
        self.folders.build = "src"

    def source(self):
        srcFile = os.path.join(
            tools.get_env("JAYSINCO_SOURCE_REPO"), "%s-%s.tar.gz" % (self.name, self.version))

        tools.unzip(srcFile, destination=self.source_folder, strip_root=True)

    def build(self):
        bootstrap_cmd = "{} {}".format(
            self._bootstrap_exe, self._bootstrap_flags)
        self.output.info(f"Running {bootstrap_cmd}")
        self.run(command=bootstrap_cmd)

        build_cmd = "{} {}".format(self._b2_exe, self._build_flags)
        self.output.info(f"Running {build_cmd}")
        self.run(command=build_cmd)

    def package(self):
        install_cmd = "{} {} install --prefix={}".format(
            self._b2_exe, self._build_flags, self.package_folder)
        self.output.info(f"Running {install_cmd}")
        self.run(command=install_cmd)

        copy(self, "LICENSE_1_0.txt", dst=os.path.join(
            self.package_folder, "licenses"), src=self.source_folder)
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Boost")

        self.cpp_info.components["disable_autolinking"].libs = []
        self.cpp_info.components["disable_autolinking"].set_property(
            "cmake_target_name", "Boost::disable_autolinking")
        self.cpp_info.components["disable_autolinking"].defines = [
            "BOOST_ALL_NO_LIB"]

        self.cpp_info.components["headers"].libs = []
        self.cpp_info.components["headers"].set_property(
            "cmake_target_name", "Boost::headers")
        self.cpp_info.components["headers"].requires.append(
            "disable_autolinking")

        self.cpp_info.components["all"].libs = collect_libs(self, folder="lib")
        self.cpp_info.components["all"].requires.append("disable_autolinking")
        if self._is_msvc:
            self.cpp_info.components["all"].system_libs.append("bcrypt")
        elif self.settings.os == "Linux":
            self.cpp_info.components["all"].system_libs.append("rt")
            self.cpp_info.components["all"].system_libs.append("pthread")

    @property
    def _b2_exe(self):
        return "b2.exe" if tools.os_info.is_windows else "b2"

    @property
    def _bootstrap_exe(self):
        return "bootstrap.bat" if tools.os_info.is_windows else "bootstrap.sh"

    @property
    def _toolset(self):
        if self._is_msvc:
            return "msvc"
        if self.settings.compiler in ["clang", "gcc"]:
            return str(self.settings.compiler)
        return None

    @property
    def _b2_architecture(self):
        if str(self.settings.arch).startswith("x86"):
            return "x86"
        return None

    @property
    def _bootstrap_flags(self):
        return "--without-libraries=python --with-toolset={}".format(self._toolset)

    @property
    def _is_msvc(self):
        return str(self.settings.compiler) in ["Visual Studio", "msvc"]

    @property
    def _b2_address_model(self):
        if str(self.settings.arch) in ("x86_64"):
            return "64"
        return "32"

    @property
    def _b2_cxxflags(self):
        cxx_flags = []
        if self.options.get_safe("fPIC"):
            cxx_flags.append("-fPIC")
        return " ".join(cxx_flags)

    @property
    def _build_flags(self):
        flags = []
        if self.settings.build_type == "Debug":
            flags.append("variant=debug")
        else:
            flags.append("variant=release")
        if self._is_msvc:
            flags.append(
                "runtime-link={}".format('static' if 'MT' in msvc_runtime_flag(self) else 'shared'))
        flags.append(f"link={'shared' if self.options.shared else 'static'}")
        flags.append(f"architecture={self._b2_architecture}")
        flags.append(f"address-model={self._b2_address_model}")
        flags.append("threading=multi")
        flags.append(f'cxxflags="{self._b2_cxxflags}"')
        flags.append(f"-j{build_jobs(self)}")
        flags.append("--abbreviate-paths")
        flags.append("--layout=system")
        flags.append("-q")
        return " ".join(flags)