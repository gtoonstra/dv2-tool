from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
import json
from models import Table, Schema, Column
import npyscreen
import logging
import curses


logging.basicConfig(filename='dv2tool.log',level=logging.DEBUG)


ENGINE='postgres'
HOST='localhost'
PORT='5432'
LOGIN='oltp_read'
PASS='oltp_read'
DB='adventureworks'

CONNECTION_FORM = "CONNECTION_FORM"
LIST_TABLE_DISPLAY = "LIST_TABLE_DISPLAY"
EDIT_STAGING_MODEL_FORM = "EDIT_STAGING_MODEL_FORM"


class MainForm(npyscreen.Form):
    def create(self):
        self.text = self.add(npyscreen.FixedText, name="Connecting to: ", value=self.parentApp.get_engine_url())
        self.conn_change_btn = self.add(npyscreen.ButtonPress, name="Change connection")
        self.process_btn = self.add(npyscreen.ButtonPress, name="Process")
        self.edit_staging_btn = self.add(npyscreen.ButtonPress, name="Edit staging")
        self.generate_btn = self.add(npyscreen.ButtonPress, name="Save and generate")

        def switch_edit_conn_form():
            self.parentApp.switchForm(CONNECTION_FORM)
        self.conn_change_btn.when_pressed_function = switch_edit_conn_form

        def run_process():
            self.parentApp.parse_schemas()
        self.process_btn.when_pressed_function = run_process

        def switch_table_list_form():
            self.parentApp.switchForm(LIST_TABLE_DISPLAY)
        self.edit_staging_btn.when_pressed_function = switch_table_list_form

        def generate():
            self.parentApp.generate()
        self.generate_btn.when_pressed_function = generate


class ConfigForm(npyscreen.ActionForm):
    def create(self):
        self.engine = self.add(npyscreen.TitleText, name = "Engine:",)
        self.host = self.add(npyscreen.TitleText, name = "Host:",)
        self.port = self.add(npyscreen.TitleText, name = "Port:",)
        self.database = self.add(npyscreen.TitleText, name = "Database:",)
        self.user = self.add(npyscreen.TitleText, name = "User:",)
        self.pw = self.add(npyscreen.TitleText, name = "Pass:",)
        self.output_dir = self.add(npyscreen.TitleText, name = "Output dir:",)

    def beforeEditing(self):
        self.engine.value = self.parentApp.engine
        self.host.value = self.parentApp.host
        self.port.value = self.parentApp.port
        self.database.value = self.parentApp.database
        self.user.value = self.parentApp.user
        self.pw.value = self.parentApp.pw
        self.output_dir = self.parentApp.output_dir

    def on_ok(self):
        self.parentApp.switchFormPrevious()

    def on_cancel(self):
        self.parentApp.switchFormPrevious()


class TableList(npyscreen.MultiLineAction):
    def __init__(self, *args, **keywords):
        super(TableList, self).__init__(*args, **keywords)

    def display_value(self, table):
        return "%s, %s" % (table.schema.name, table.name)

    def actionHighlighted(self, act_on_this, keypress):
        self.parent.parentApp.getForm(EDIT_STAGING_MODEL_FORM).table = act_on_this
        self.parent.parentApp.switchForm(EDIT_STAGING_MODEL_FORM)


class StagingTablesDisplay(npyscreen.FormMutt):
    MAIN_WIDGET_CLASS = TableList
    def beforeEditing(self):
        self.update_list()

    def update_list(self):
        self.wMain.values = self.parentApp.get_tables()
        self.wMain.display()


class EditStagingForm(npyscreen.ActionForm):
    def create(self):
        self.table = None
        self.schema = self.add(npyscreen.TitleFixedText, name = "Schema:",)
        self.table_field = self.add(npyscreen.TitleFixedText, name = "Table:",)
        self.selected_cols = self.add(npyscreen.TitleMultiSelect, name = "Selected cols:",)
        #self.business_key = self.add(npyscreen.TitleMultiSelect, name = "Business keys:",)

    def beforeEditing(self):
        self.schema.value = self.table.schema.name
        self.table_field.value = self.table.name
        self.selected_cols.values = self.table.get_column_list()
        #self.business_key.values = self.table.get_column_list()

    def on_ok(self):
        self.table.set_selected(self.selected_cols.value)
        # self.table.set_business_keys(self.business_key.value)
        self.parentApp.switchFormPrevious()

    def on_cancel(self):
        self.parentApp.switchFormPrevious()


class TestApp(npyscreen.NPSAppManaged):
    def __init__(self):
        super().__init__()
        self.schemas = {}
        self.engine = ENGINE
        self.host = HOST
        self.port = PORT
        self.user = LOGIN
        self.pw = PASS
        self.database = DB
        self.output_dir = '/tmp/example'

    def onStart(self):
        self.addForm("MAIN", MainForm)
        self.addForm(CONNECTION_FORM, ConfigForm)
        self.addForm(LIST_TABLE_DISPLAY, StagingTablesDisplay)
        self.addForm(EDIT_STAGING_MODEL_FORM, EditStagingForm)

    def get_engine_url(self):
        return '{0}://{1}:{2}@{3}:{4}/{5}'.format(
            self.engine,
            self.user,
            self.pw,
            self.host,
            self.port,
            self.database)

    def count_tables(self):
        count = 0
        for schema_name, schema in self.schemas.items():
            count += schema.count_tables()
        return count

    def get_tables(self):
        tables = []
        for schema_name, schema in self.schemas.items():
            tables += schema.get_tables()
        return tables

    def parse_schemas(self):
        engine = create_engine(self.get_engine_url())
        insp = reflection.Inspector.from_engine(engine)

        self.schemas = {}
        for schema_name in insp.get_schema_names():
            if schema_name == 'information_schema':
                continue
            self.schemas[schema_name] = Schema(schema_name)
            self.schemas[schema_name].parse(engine)

        for schema_name, schema in self.schemas.items():
            schema.resolve_foreign_keys(self.schemas)
            schema.guess_business_keys()

    def generate(self):
        for schema_name, schema in self.schemas.items():
            schema.generate_selects(self.output_dir)


if __name__ == "__main__":
    app = TestApp()
    app.run()
