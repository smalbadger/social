import os

facile_dir = os.path.abspath("../")
src_dir = os.path.abspath("../src/")

icons_dir = os.path.abspath("../resources")
icons_resouce_file = os.path.abspath("../icons.qrc")

wrapper = """
<RCC>
    <qresource prefix="/icon">
        {file_list}
    </qresource>
</RCC>
"""

file_list_item = """
        <file alias="{alias}">{filepath}</file>
"""


if __name__ == "__main__":
	print("Compiling icons.qrc file")
	file_list = ""
	for root, dirs, files in os.walk(icons_dir):
		for file in files:
			fpath = os.path.join(root, file)
			from_facile = os.path.relpath(fpath, facile_dir)
			from_src = os.path.relpath(fpath, src_dir)
			file_list += file_list_item.format(alias=from_src, filepath=from_facile)
			
	qrc_contents = wrapper.format(file_list=file_list).replace("\\", "/")
	
	with open(icons_resouce_file, "w") as icons_file:
		icons_file.write(qrc_contents)

