
from os import makedirs
from os.path import join, isdir
from platform import system
from subprocess import call

from SCons.Script import AlwaysBuild, Builder, Default, DefaultEnvironment


env = DefaultEnvironment()


env.Replace(
    AR="tricore-elf-ar",
    AS="tricore-elf-as",
    CC="tricore-elf-gcc",
    CXX="tricore-elf-g++",
    OBJCOPY="tricore-elf-objcopy",
    SIZETOOL="tricore-elf-size",
    OBJDUMP="tricore-elf-objdump",
    RANLIB="tricore-elf-ranlib",

    SIZEPRINTCMD='$SIZETOOL -d $SOURCES',
    PROGSUFFIX=".elf"
)

if env.get("PROGNAME", "program") == "program":
   env.Replace(PROGNAME="firmware")

env.Append(


    ASFLAGS=[
        "-Wa,", "--gdwarf-2", "-mtc161"],

    CFLAGS=[
        "-c",
        "-fno-common",
        "-O2",
        "-g3",
        "-W",
        "-Wextra",
        "-Wdiv-by-zero",
        "-Warray-bounds",
        "-Wcast-align",
        "-Wignored-qualifiers",
        "-Wformat",
        "-Wformat-security",
        "-fshort-double",
        "-include", 
        "Variant.h",
        "-mversion-info",
        "-mcpu=%s" % env.BoardConfig().get("build.cpu")
    ],

    CXXFLAGS=[
        "-std=c++14",
        "-fno-common",
        "-O2",
        "-g3",
        "-W",
        "-Wextra",
        "-Wdiv-by-zero",
        "-Warray-bounds",
        "-Wcast-align",
        "-Wignored-qualifiers",
        "-Wformat",
        "-Wformat-security",
        "-fshort-double",
        "-include", 
        "Variant.h",
        "-mversion-info",
        "-mcpu=%s" % env.BoardConfig().get("build.cpu")
    ],

    LINKFLAGS=[
        "-nocrt0",
        "-Wl,--gc-sections",
        '"-Wl,-Map=' + join("$BUILD_DIR", "${PROGNAME}.map") + '"',
        "-Wl,--cref",
        "-Wl,--gc-sections",
        "-fshort-double",
        "-Wl,--mem-holes",
        "-mcpu=%s" % env.BoardConfig().get("build.cpu")
    ],


    BUILDERS=dict(
        ElfToLst=Builder(
            action=" ".join([
                "$OBJDUMP",
                "-S",
                "-d",
                "$SOURCES",
                ">$TARGET"]),
            suffix=".lst"
        ),
        ElfToHex=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "ihex",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".hex"
        )
    )
)

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
    target_firm = join("$BUILD_DIR", "${PROGNAME}.hex")
else:
    target_elf = env.BuildProgram()
    target_firm = env.ElfToHex(join("$BUILD_DIR", "${PROGNAME}"), target_elf)

AlwaysBuild(env.Alias("nobuild", target_firm))
target_buildprog = env.Alias("buildprog", target_firm, target_firm)



#
# Target: Print binary size
#
target_size = env.Alias(
    "size", target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"))
AlwaysBuild(target_size)



#
# Target: Upload firmware
#
######################## Target reset post upload ######################
TOOL_DIR = env.PioPlatform().get_package_dir("tool-memtool")


def after_upload(source, target, env):
    print("Reset target")
    call(join(TOOL_DIR, "utils_platformio", "resetTc275.exe"))


env.AddPostAction("upload", after_upload)
########################################################################


#########debug_tools = env.BoardConfig().get("debug.tools", {})%s,%s" %
upload_protocol = env.subst("$UPLOAD_PROTOCOL")


def _imtmemtool_cmd_script(env):
    build_dir = env.subst("$BUILD_DIR")
    firmwarePath = join(build_dir, "firmware.hex")
    if not isdir(build_dir):
        makedirs(build_dir)
    script_path = join(build_dir, "upload.mtb")
    commands = [
        "open_file %s" % firmwarePath,
        "connect",
        "select_all_sections",
        "add_selected_sections",
        "program",
        "disconnect",
        "exit"
    ]
    with open(script_path, "w") as fp:
        fp.write("\n".join(commands))
    return script_path


env.Replace(
    __imtmemtool_cmd_script=_imtmemtool_cmd_script,
    UPLOADER="IMTmemtool.exe" if system() == "Windows" else "IMTMemtool",
    UPLOADERFLAGS=["-c",
                   join(TOOL_DIR, "utils_platformio", "Aurduino_TC27xD_das.cfg")],
    UPLOADCMD='$UPLOADER $UPLOADERFLAGS "${__imtmemtool_cmd_script(__env__)}"'
)

upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]
AlwaysBuild(env.Alias("upload", target_firm, upload_actions))


#
# Target: Define targets
#
Default([target_buildprog, target_size])