from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
import json
from models import Table, Schema, Column
import npyscreen


TYPE='postgres'
HOST='localhost'
PORT=5432
LOGIN='oltp_read'
PASS='oltp_read'
DB='adventureworks'


engine_url = '{0}://{1}:{2}@{3}:{4}/{5}'.format(
    TYPE,
    LOGIN,
    PASS,
    HOST,
    PORT,
    DB)


engine = create_engine(engine_url)
insp = reflection.Inspector.from_engine(engine)
output_dir = '/tmp/example'

class TestApp(npyscreen.NPSApp):
    def __init__(self):
        super().__init__()

        self.schemas = {}
        for schema_name in insp.get_schema_names():
            if schema_name == 'information_schema':
                continue
            self.schemas[schema_name] = Schema(schema_name)
            self.schemas[schema_name].parse(engine)

        for schema_name, schema in self.schemas.items():
            schema.resolve_foreign_keys(self.schemas)
            schema.guess_business_keys()

    def main(self):
        # These lines create the form and populate it with widgets.
        # A fairly complex screen in only 8 or so lines of code - a line for each control.
        F  = npyscreen.Form(name = "Welcome to Npyscreen",)
        t  = F.add(npyscreen.TitleText, name = "Text:",)
        fn = F.add(npyscreen.TitleFilename, name = "Filename:")
        fn2 = F.add(npyscreen.TitleFilenameCombo, name="Filename2:")
        dt = F.add(npyscreen.TitleDateCombo, name = "Date:")
        s  = F.add(npyscreen.TitleSlider, out_of=12, name = "Slider")
        ml = F.add(npyscreen.MultiLineEdit,
               value = """try typing here!\nMutiline text, press ^R to reformat.\n""",
               max_height=5, rely=9)
        ms = F.add(npyscreen.TitleSelectOne, max_height=4, value = [1,], name="Pick One",
                values = ["Option1","Option2","Option3"], scroll_exit=True)
        ms2= F.add(npyscreen.TitleMultiSelect, max_height =-2, value = [1,], name="Pick Several",
                values = ["Option1","Option2","Option3"], scroll_exit=True)

        # This lets the user interact with the Form.
        F.edit()

        self.generate()

    def generate(self):
        print("Generating sql")
        for schema_name, schema in self.schemas.items():
            schema.generate_selects(output_dir)


if __name__ == "__main__":
    app = TestApp()
    app.run()
