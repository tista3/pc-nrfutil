# Copyright (c) 2015, Nordic Semiconductor
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of Nordic Semiconductor ASA nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from nordicsemi.dfu import intelhex


class nRFHex(intelhex.IntelHex):
    """
        Converts and merges .hex and .bin files into one .bin file.
    """

    mbr_end_address = 0x1000

    def __init__(self, source, bootloader=None):
        """
        Constructor that requires a firmware file path.
        Softdevices can take an optional bootloader file path as parameter.

        :param str source: The file path for the firmware
        :param str bootloader: Optional file path to bootloader firmware
        :return: None
        """
        super(nRFHex, self).__init__()

        self.file_format = 'hex'

        if source.endswith('.bin'):
            self.file_format = 'bin'

        self.loadfile(source, self.file_format)

        self._removeuicr()

        self.bootloaderhex = None

        if bootloader is not None:
            self.bootloaderhex = nRFHex(bootloader)

    def _removeuicr(self):
        uicr_start_address = 0x10000000
        maxaddress = self.maxaddr()
        if maxaddress >= uicr_start_address:
            for i in range(uicr_start_address, maxaddress + 1):
                self._buf.pop(i, 0)

    def minaddr(self):
        min_address = super(nRFHex, self).minaddr()

        # Addresses lower than 0x1000 are reserved for master boot record
        if self.file_format != 'bin':
            min_address = max(nRFHex.mbr_end_address, min_address)

        return min_address

    def size(self):
        """
        Returns the size of the source.
        :return: int
        """
        min_address = self.minaddr()
        max_address = self.maxaddr()

        size = max_address - min_address + 1

        # Round up to nearest word
        word_size = 4
        number_of_words = (size + (word_size - 1)) / word_size
        size = number_of_words * word_size

        return size

    def bootloadersize(self):
        """
        Returns the size of the bootloader.
        :return: int
        """
        if self.bootloaderhex is None:
            return 0

        return self.bootloaderhex.size()

    def tobinfile(self, fobj):
        """
        Writes a binary version of source and bootloader respectivly to fobj which could be a
        file object or a file path.

        :param str fobj: File path or object the function writes to
        :return: None
        """
        # If there is a bootloader this will make the recursion call use the samme file object.
        if getattr(fobj, "write", None) is None:
            fobj = open(fobj, "wb")
            close_fd = True
        else:
            close_fd = False

        start_address = self.minaddr()
        size = self.size()
        super(nRFHex, self).tobinfile(fobj, start=start_address, size=size)

        if self.bootloaderhex is not None:
            self.bootloaderhex.tobinfile(fobj)

        if close_fd:
            fobj.close()
