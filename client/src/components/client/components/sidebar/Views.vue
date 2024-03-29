<template>
  <div>
    <!----------->
    <!-- VIEWS -->
    <!----------->
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; padding-bottom:3px">{{ dialogOptions.icon }}</v-icon>{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-bottom:10px">
                  <div v-if="dialogOptions.text.length > 0" class="body-1">{{ dialogOptions.text }}</div>
                  <div v-if="dialogOptions.mode == 'createView'">
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.name" :rules="[v => !!v || '']" label="View Name" autofocus required style="padding-top:8px;"></v-text-field>
                    <div style="margin-left:auto; margin-right:auto; height:40vh; width:100%; margin-bottom:15px;">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'renameView'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current Name" required></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New Name" autofocus required hide-details style="padding-top:0px; padding-bottom:5px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'duplicateView'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current Name" required></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New Name" autofocus required hide-details style="padding-top:0px; padding-bottom:5px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'deleteView'">
                    <v-card style="margin-top:15px; margin-bottom:15px">
                      <v-list>
                        <v-list-item v-for="item in sidebarSelected" :key="item.key" style="min-height:35px">
                          <v-list-item-content style="padding:0px">
                            <v-list-item-title>{{ item.name }}</v-list-item-title>
                          </v-list-item-content>
                        </v-list-item>
                      </v-list>
                    </v-card>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogOptions.submit.length > 0" cols="auto" style="margin-right:5px">
                      <v-btn :loading="loading" @click="dialogSubmit" color="#00b16a">{{ dialogOptions.submit }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogOptions.cancel.length > 0">
                      <v-btn :disabled="loading" @click="dialog = false" color="#EF5354">{{ dialogOptions.cancel }}</v-btn>
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
import ace from 'ace-builds';

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
      'settings',
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'database',
      'sidebarOpened',
      'sidebarSelected',
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('click-contextmenu-view', this.contextMenuClicked);
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
      if (!val) return
      if (this.dialogEditor == null && this.dialogOptions.mode == 'createView') this.initEditor()
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
          mode: "mysql",
          theme: "ace/theme/monokai",
          keyboardHandler: "ace/keyboard/vscode",
          fontSize: parseInt(this.settings['font_size']) || 14,
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
        let placeholder = '/* SELECT * FROM tbl; */'
        this.dialogEditor.setValue(placeholder, -1)
        this.dialogEditor.on("focus", () => {
          if (this.dialogEditor.getValue() == placeholder) this.dialogEditor.setValue('')
        })
        this.dialogEditor.on("blur", () => {
          if (this.dialogEditor.getValue().length == 0) this.dialogEditor.setValue(placeholder, -1)
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
      else if (item == 'Rename View') this.renameView()
      else if (item == 'Duplicate View') this.duplicateView()
      else if (item == 'Delete View') this.deleteView()
      else if (item == 'Export View') this.exportView()
      else if (item == 'Clone View') this.cloneView()
      else if (item == 'Copy View Name') this.copyViewNameSubmit()
      else if (item == 'Copy View Syntax') this.copyViewSyntaxSubmit()
    },
    createView() {
      let dialogOptions = { 
        mode: 'createView', 
        icon: 'fas fa-plus',
        title: 'CREATE VIEW', 
        text: '', 
        item: { name: '' }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      if (this.dialogEditor != null) this.dialogEditor.setValue('/* SELECT * FROM tbl; */', -1)
      this.dialog = true
    },
    renameView() {
      let dialogOptions = { 
        mode: 'renameView', 
        icon: 'fas fa-feather-alt',
        title: 'RENAME VIEW', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    duplicateView() {
      let dialogOptions = { 
        mode: 'duplicateView', 
        icon: 'fas fa-clone',
        title: 'DUPLICATE VIEW', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    deleteView() {
      let dialogOptions = { 
        mode: 'deleteView', 
        icon: 'fas fa-minus',
        title: 'DELETE VIEW', 
        text: "Are you sure you want to delete the selected views? This operation cannot be undone.",
        item: {}, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    exportView() {
      const items = this.sidebarSelected.map(x => x.name)
      EventBus.$emit('show-bottombar-objects-export', { object: 'views', items })
    },
    cloneView() {
      const items = this.sidebarSelected.map(x => x.name)
      EventBus.$emit('show-bottombar-objects-clone', { object: 'views', items })
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      this.loading = true
      if (this.dialogOptions.mode == 'createView') this.createViewSubmit()
      else if (this.dialogOptions.mode == 'renameView') this.renameViewSubmit() 
      else if (this.dialogOptions.mode == 'duplicateView') this.duplicateViewSubmit() 
      else if (this.dialogOptions.mode == 'deleteView') this.deleteViewSubmit()
    },
    createViewSubmit() {
      let viewName = this.dialogOptions.item.name
      let query = "CREATE VIEW `" + viewName.replaceAll('`','``') + "` AS " + this.dialogEditor.getValue()
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created table
          this.sidebarSelected = [{ id: 'view|' + viewName, name: viewName, type: 'View' }]
          // Open sidebar parent
          this.sidebarOpened = ['views']
          // Change view to Content
          this.headerTab = 2
          this.headerTabSelected = 'content'
          EventBus.$emit('get-content')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    renameViewSubmit() {
      let currentName = this.contextMenuItem.name
      let newName = this.dialogOptions.item.newName
      let query = "RENAME TABLE `" + currentName.replaceAll('`','``') + "` TO `" + newName.replaceAll('`','``') + "`;"
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select renamed table
          this.sidebarSelected = [{ id: 'view|' + newName, name: newName, type: 'View' }]
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    duplicateViewSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let query = "SHOW CREATE VIEW `" + currentName.replaceAll('`','``') + "`;"
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then((res) => { 
        let syntax = 'SELECT ' + JSON.parse(res.data)[0].data[0]['Create View'].split(' AS select ')[1]
        let query = "CREATE VIEW `" + newName.replaceAll('`','``') + "` AS " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('execute-sidebar', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = [{ id: 'view|' + newName, name: newName, type: 'View' }]
            // Change view to Content
            this.headerTab = 2
            this.headerTabSelected = 'content'
            EventBus.$emit('get-content')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    deleteViewSubmit() {
      let queries = []
      for (let item of this.sidebarSelected) queries.push("DROP VIEW `" + item.name.replaceAll('`','``') + "`;")
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Unselect deleted view
          this.sidebarSelected = []
          // Change view to Client
          this.headerTab = 0
          this.headerTabSelected = 'client'
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    copyViewNameSubmit() {
      const name = this.contextMenuItem.name
      this.copyToClipboard(name)
      EventBus.$emit('send-notification', 'Copied to clipboard.', '#00b16a', 1)
    },
    copyViewSyntaxSubmit() {
      let name = this.contextMenuItem.name
      let query = "SHOW CREATE VIEW `" + name.replaceAll('`','``') + "`;"
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create View'] + ';'
        this.copyToClipboard(syntax)
        EventBus.$emit('send-notification', 'Copied to clipboard.', '#00b16a', 1)
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    copyToClipboard(textToCopy) {
      if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(textToCopy)
      else {
        let textArea = document.createElement("textarea")
        textArea.value = textToCopy
        textArea.style.position = "absolute"
        textArea.style.opacity = 0
        document.body.appendChild(textArea)
        textArea.select()
        return new Promise((res, rej) => {
          document.execCommand('copy') ? res() : rej()
          textArea.remove()
        })
      }
    },
  }
}
</script>