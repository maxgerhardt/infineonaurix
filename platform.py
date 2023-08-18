from platformio.managers.platform import PlatformBase

class InfineonaurixPlatform(PlatformBase):
    def configure_default_packages(self, variables, targets):
        board = variables.get("board")
        board_config = self.board_config(board)
        # check platformio.ini options first, then what's written in the board JSON config
        used_toolchain = variables.get("board_build.toolchain", board_config.get("build.toolchain"))
        if used_toolchain == "hightec":
            self.packages["toolchain-hightec"]["optional"] = False
        else:
            self.packages["toolchain-tricore_gcc494"]["optional"] = False
        return PlatformBase.configure_default_packages(self, variables,
                                                       targets)