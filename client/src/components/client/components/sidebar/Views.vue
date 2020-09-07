<template>
  <div>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar v-if="dialogOptions.text.length == 0" flat color="primary">
          <v-toolbar-title class="white--text">{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div v-if="dialogOptions.text.length > 0" class="text-h6" style="font-weight:400;"> {{ dialogOptions.title }}</div>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div v-if="dialogOptions.text.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogOptions.text }}</div>
                  <div v-if="dialogOptions.mode == 'createView'">
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.name" :rules="[v => !!v || '']" label="View Name" autofocus required style="padding-top:0px;"></v-text-field>
                    <div style="margin-left:auto; margin-right:auto; height:40vh; width:100%">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogOptions.submit.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="primary">{{ dialogOptions.submit }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogOptions.cancel.length > 0" style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">{{ dialogOptions.cancel }}</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import * as ace from 'ace-builds';
import 'ace-builds/webpack-resolver';
import 'ace-builds/src-noconflict/ext-language_tools';

import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      dialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' },
      dialogEditor: null,
    }
  },
  props: { contextMenuItem: Object },
  computed: {
    ...mapFields([
      'database',
      'treeview',
      'treeviewOpened',
      'treeviewSelected',
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('CLICK_CONTEXTMENU_VIEW', this.contextMenuClicked);
  },
  watch: {
    dialog (val) {
      if (!val) return
      if (this.dialogEditor == null) this.initEditor()
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
  },
  methods: {
    initEditor() {
      this.$nextTick(() => {
        // Editor Settings
        this.dialogEditor = ace.edit("dialogEditor", {
          mode: "ace/mode/sql",
          theme: "ace/theme/monokai",
          fontSize: 14,
          showPrintMargin: false,
          wrap: true,
          autoScrollEditorIntoView: true,
          enableBasicAutocompletion: true,
          enableLiveAutocompletion: true,
          enableSnippets: false,
          highlightActiveLine: false
        });
        this.dialogEditor.session.setOptions({ tabSize: 4, useSoftTabs: false })

        // Add default value + placeholder
        this.dialogEditor.setValue('/* SELECT * FROM tbl; */', -1)
        this.dialogEditor.on("focus", () => {
          if (this.dialogEditor.getValue() == '/* SELECT * FROM tbl; */') this.dialogEditor.setValue('')
        })
        this.dialogEditor.on("blur", () => {
          if (this.dialogEditor.getValue().length == 0) this.dialogEditor.setValue('/* SELECT * FROM tbl; */', -1)
        })

        // Add custom keybinds
        this.dialogEditor.container.addEventListener("keydown", (e) => {
          // - Increase Font Size -
          if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault()
            let size = parseInt(this.dialogEditor.getFontSize(), 10) || 12
            this.dialogEditor.setFontSize(size + 1)
          }
          // - Decrease Font Size -
          else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault()
            let size = parseInt(this.dialogEditor.getFontSize(), 10) || 12
            this.dialogEditor.setFontSize(Math.max(size - 1 || 1))
          }
        }, false);
      })
    },
    contextMenuClicked(item) {
      if (item == 'Create View') this.createView()
    },
    createView() {
      let dialogOptions = { 
        mode: 'createView', 
        title: 'Create View', 
        text: '', 
        item: { name: '' }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      if (this.dialogEditor != null) this.dialogEditor.setValue('/* SELECT * FROM tbl; */', -1)
      this.dialog = true
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      this.loading = true
      if (this.dialogOptions.mode == 'createView') this.createViewSubmit()
    },
    createViewSubmit() {
      let viewName = this.dialogOptions.item.name
      let query = "CREATE VIEW " + viewName + " AS " + this.dialogEditor.getValue()
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created table
          this.treeviewSelected = { id: 'view|' + viewName, name: viewName, type: 'View' }
          this.treeview = ['view|' + viewName]
          // Open treeview parent
          this.treeviewOpened = ['views']
          // Change view to Content
          this.headerTab = 2
          this.headerTabSelected = 'content'
          EventBus.$emit('GET_CONTENT')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
  }
}
</script>