from conans import ConanFile, CMake, tools
import shutil
import os.path


class FclConan(ConanFile):
    name = "fcl"
    version = "0.5.0"
    license = "BSD"
    author = "Mohamed G.A. Ghita (mohamed.ghita@radalytica.com)"
    url = "https://github.com/mohamedghita/conan-fcl"
    description = "conan.io package for flexible-collision-library/fcl https://github.com/flexible-collision-library/fcl"
    topics = ("fcl", "collision")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "build_tests": [True, False]
    }
    default_options = {
        "shared": True,
        "build_tests": False
    }
    requires = "eigen/3.3.7@conan/stable", "libccd/2.1@radalytica/stable"
    build_requires = "cmake_installer/[>=3.14.4]@conan/stable"
    generators = "cmake"

    def source(self):
        extension = ".zip" if tools.os_info.is_windows else ".tar.gz"
        url = "https://github.com/flexible-collision-library/fcl/archive/%s%s" % (self.version, extension)
        tools.get(url)
        shutil.move("fcl-%s" % self.version, "fcl")
        tools.replace_in_file("fcl/CMakeLists.txt", "project(fcl CXX C)",
                              'project(fcl CXX C)\n' +
                              'include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)\n' +
                              'conan_basic_setup()\n')

    def _fcl_cmake_definitions(self, package_folder, build_folder):
        # CCD_LIBRARY_DIRS
        cmake_defs = {}
        cmake_defs["CCD_INCLUDE_DIRS"] = self.deps_cpp_info["libccd"].includedirs
        cmake_defs["CCD_LIBRARY_DIRS"] = self.deps_cpp_info["libccd"].libdirs
        cmake_defs["FCL_BUILD_TESTS"] = 'ON' if self.options.build_tests else 'OFF'
        cmake_defs["FCL_STATIC_LIBRARY"] = 'OFF' if self.options.shared else 'ON'

        if build_folder:
            cmake_defs['EXECUTABLE_OUTPUT_PATH'] = os.path.join(build_folder, "bin")  # points to testing executables. testing is executed during conan build
        if package_folder:
            cmake_defs["CMAKE_INSTALL_PREFIX"] = package_folder

        return cmake_defs

    def _configure_cmake(self, package_folder=None, build_folder=None):
        WARNING_FLAGS = ''  # '-Wall -Wextra -Wnon-virtual-dtor -pedantic -Wshadow'
        if self.settings.build_type == "Debug":
            # debug flags
            cppDefines = '-DDEBUG'
            cFlags = '-g' + ' ' + WARNING_FLAGS
            cxxFlags = cFlags + ' ' + cppDefines
            linkFlags = ''
        else:
            # release flags
            cppDefines = '-DNDEBUG'
            cFlags = '-v -O3 -s' + ' ' + WARNING_FLAGS
            cxxFlags = cFlags + ' ' + cppDefines
            linkFlags = '-s'  # Strip symbols
        cmake = CMake(self)
        cmake.verbose = False

        # put definitions here so that they are re-used in cmake between
        # build() and package()
        cmake.definitions["CONAN_C_FLAGS"] += ' ' + cFlags
        cmake.definitions["CONAN_CXX_FLAGS"] += ' ' + cxxFlags
        cmake.definitions["CONAN_SHARED_LINKER_FLAGS"] += ' ' + linkFlags
        cmake_defs = self._fcl_cmake_definitions(package_folder, build_folder)
        cmake_defs["CMAKE_POSITION_INDEPENDENT_CODE"] = "ON"
        cmake.configure(defs=cmake_defs, source_folder=os.path.join(self.build_folder, "fcl"))
        return cmake

    def build(self):
        vars = {'PKG_CONFIG_PATH': os.path.join(self.deps_cpp_info["libccd"].rootpath, 'lib', 'pkgconfig')}
        with tools.environment_append(vars):
            cmake = self._configure_cmake(build_folder=self.build_folder)
            cmake.build()
            if self.options.build_tests:
                cmake.test()

    def package(self):
        cmake = self._configure_cmake(package_folder=self.package_folder)
        cmake.install()

    def package_info(self):
        self.cpp_info.includedirs = ['include']  # Ordered list of include paths
        self.cpp_info.libs = [self.name]  # The libs to link against
        self.cpp_info.libdirs = ['lib']  # Directories where libraries can be found
