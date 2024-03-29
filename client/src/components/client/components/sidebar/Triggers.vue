<template>
  <div>
    <!-------------->
    <!-- TRIGGERS -->
    <!-------------->
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
                  <div v-if="dialogOptions.mode == 'createTrigger'">
                    <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus :rules="[v => !!v || '']" required style="padding-top:8px"></v-text-field>
                    <v-select v-model="dialogOptions.item.time" :items="['Before','After']" :rules="[v => !!v || '']" label="Action Time" required style="padding-top:0px;"></v-select>
                    <v-select v-model="dialogOptions.item.event" :items="['Insert','Update','Delete']" :rules="[v => !!v || '']" label="Event" required style="padding-top:0px;"></v-select>
                    <v-select v-model="dialogOptions.item.table" :items="tableItems" :rules="[v => !!v || '']" label="Table" required style="padding-top:0px;"></v-select>
                    <div style="margin-left:auto; margin-right:auto; height:35vh; width:100%; margin-bottom:15px;">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'renameTrigger'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current Name" required></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New Name" autofocus required hide-details style="padding-top:0px; padding-bottom:5px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'duplicateTrigger'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current Name" required></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New Name" autofocus required hide-details style="padding-top:0px; padding-bottom:5px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'deleteTrigger'">
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
                <div style="margin-top:15px">
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
      'tableItems',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('click-contextmenu-trigger', this.contextMenuClicked);
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
      if (!val) return
      if (this.dialogEditor == null && this.dialogOptions.mode == 'createTrigger') this.initEditor()
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
          mode: "ace/mode/mysql",
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
      if (item == 'Create Trigger') this.createTrigger()
      else if (item == 'Rename Trigger') this.renameTrigger()
      else if (item == 'Duplicate Trigger') this.duplicateTrigger()
      else if (item == 'Delete Trigger') this.deleteTrigger()
      else if (item == 'Export Trigger') this.exportTrigger()
      else if (item == 'Clone Trigger') this.cloneTrigger()
      else if (item == 'Copy Trigger Name') this.copyTriggerNameSubmit()
      else if (item == 'Copy Trigger Syntax') this.copyTriggerSyntaxSubmit()
    },
    createTrigger() {
      let dialogOptions = { 
        mode: 'createTrigger', 
        icon: 'fas fa-plus',
        title: 'CREATE TRIGGER', 
        text: '', 
        item: { name: '', table: '', time: '', event: '' }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      if (this.dialogEditor != null) this.dialogEditor.setValue('')
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    renameTrigger() {
      let dialogOptions = { 
        mode: 'renameTrigger', 
        icon: 'fas fa-feather-alt',
        title: 'RENAME TRIGGER', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    duplicateTrigger() {
      let dialogOptions = { 
        mode: 'duplicateTrigger', 
        icon: 'fas fa-clone',
        title: 'DUPLICATE TRIGGER', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    deleteTrigger() {
      let dialogOptions = { 
        mode: 'deleteTrigger', 
        icon: 'fas fa-minus',
        title: 'DELETE TRIGGER', 
        text: "Are you sure you want to delete the selected triggers? This operation cannot be undone.",
        item: {}, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    exportTrigger() {
      const items = this.sidebarSelected.map(x => x.name)
      EventBus.$emit('show-bottombar-objects-export', { object: 'triggers', items })
    },
    cloneTrigger() {
      const items = this.sidebarSelected.map(x => x.name)
      EventBus.$emit('show-bottombar-objects-clone', { object: 'triggers', items })
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      this.loading = true
      if (this.dialogOptions.mode == 'createTrigger') this.createTriggerSubmit()
      else if (this.dialogOptions.mode == 'renameTrigger') this.renameTriggerSubmit() 
      else if (this.dialogOptions.mode == 'duplicateTrigger') this.duplicateTriggerSubmit() 
      else if (this.dialogOptions.mode == 'deleteTrigger') this.deleteTriggerSubmit() 
    },
    createTriggerSubmit() {
      let triggerName = this.dialogOptions.item.name
      let triggerCode = this.dialogEditor.getValue().endsWith(';') ? this.dialogEditor.getValue() : this.dialogEditor.getValue() + ';'
      let query = "CREATE TRIGGER `" + triggerName.replaceAll('`','``') + '` ' + this.dialogOptions.item.time + ' ' + this.dialogOptions.item.event + ' ON ' + this.dialogOptions.item.table + ' FOR EACH ROW BEGIN\n' + triggerCode + '\nEND;'
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created trigger
          this.sidebarSelected = [{ id: 'trigger|' + triggerName, name: triggerName, type: 'Trigger' }]
          // Open sidebar parent
          this.sidebarOpened = ['triggers']
          // Change view to Info
          this.headerTab = 3
          this.headerTabSelected = 'info_trigger'
          EventBus.$emit('get-info', 'trigger')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    renameTriggerSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE TRIGGER `" + currentName.replaceAll('`','``') + "`", "DROP TRIGGER IF EXISTS `" + currentName.replaceAll('`','``') + "`"]
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['SQL Original Statement'].split(' TRIGGER ' + currentName.replaceAll('`','``') + ' ')[1]
        let query = "CREATE TRIGGER `" + newName.replaceAll('`','``') + "` " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('execute-sidebar', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = [{ id: 'trigger|' + newName, name: newName, type: 'Trigger' }]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_trigger'
            EventBus.$emit('get-info', 'trigger')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    duplicateTriggerSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE TRIGGER `" + currentName.replaceAll('`','``') + "`"]
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['SQL Original Statement'].split(' TRIGGER ' + currentName.replaceAll('`','``') + ' ')[1]
        let query = "CREATE TRIGGER `" + newName.replaceAll('`','``') + "` " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('execute-sidebar', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = [{ id: 'trigger|' + newName, name: newName, type: 'Trigger' }]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_trigger'
            EventBus.$emit('get-info', 'trigger')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    deleteTriggerSubmit() {
      let queries = []
      for (let item of this.sidebarSelected) queries.push("DROP TRIGGER `" + item.name.replaceAll('`','``') + "`;")
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
    copyTriggerNameSubmit() {
      let name = this.contextMenuItem.name
      this.copyToClipboard(name)
      EventBus.$emit('send-notification', 'Copied to clipboard.', '#00b16a', 1)
    },
    copyTriggerSyntaxSubmit() {
      let name = this.contextMenuItem.name
      let query = "SHOW CREATE TRIGGER `" + name.replaceAll('`','``') + "`;"
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['SQL Original Statement'] + ';'
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