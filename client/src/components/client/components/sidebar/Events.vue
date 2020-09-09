<template>
  <div>
    <!------------>
    <!-- EVENTS -->
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
                  <div v-if="dialogOptions.mode == 'createEvent'">
                    <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus :rules="[v => !!v || '']" required hide-details style="padding-top:0px;"></v-text-field>
                    <v-radio-group v-model="dialogOptions.item.timing" hide-details style="margin-top:20px;">
                      <v-row no-gutters>
                        <v-col cols="auto">
                          <div class="text-subtitle-1 font-weight-medium" style="margin-right:15px;">SCHEDULE:</div>
                        </v-col>
                        <v-col cols="auto" style="margin-top:2px">
                          <v-radio label="One-time event" value="0"></v-radio>
                        </v-col>
                        <v-col cols="auto" style="margin-top:2px; margin-left:15px;">
                          <v-radio label="Repeating event" value="1"></v-radio>
                        </v-col>
                      </v-row>
                    </v-radio-group>
                    <v-card style="margin-top:15px;">
                      <v-card-text>
                        <div v-if="dialogOptions.item.timing == '0'">
                          <v-row no-gutters style="height:50px;">
                            <v-col cols="auto">
                              <div class="body-1" style="margin-top:14px">Execute at:</div>
                            </v-col>
                            <v-col cols="3" style="margin-left:10px">
                              <v-text-field solo v-model="dialogOptions.item.executedAt" label="" :rules="[v => !!v || '']" required hide-details style="padding-top:0px;"></v-text-field>
                            </v-col>
                            <v-col cols="auto" style="margin-left:10px">
                              <v-checkbox v-model="dialogOptions.item.interval" label="Interval" hide-details class="body-1" style="padding:0px; margin-top:14px;"></v-checkbox>
                            </v-col>
                            <v-col style="margin-top:3px; margin-left:10px;">
                              <v-text-field :disabled="!dialogOptions.item.interval" solo v-model="dialogOptions.item.intervalValue" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                            </v-col>
                            <v-col style="margin-top:3px; margin-left:10px;">
                              <v-select :disabled="!dialogOptions.item.interval" solo v-model="dialogOptions.item.intervalOptions" :items="interval" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                            </v-col>
                          </v-row>
                        </div>
                        <div v-else>
                          <v-row no-gutters style="height:50px;">
                            <v-col cols="auto" style="margin-right:10px;">
                              <div class="body-1" style="margin-top:14px">Execute every:</div>
                            </v-col>
                            <v-col cols="3">
                              <v-text-field solo v-model="dialogOptions.item.executedEvery" label="" :rules="[v => !!v || '']" required hide-details style="padding-top:0px;"></v-text-field>
                            </v-col>
                            <v-col style="margin-left:10px;">
                              <v-select solo v-model="dialogOptions.item.intervalOptions" :items="['SECOND','MINUTE','HOUR']" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                            </v-col>
                          </v-row>
                          <v-row no-gutters style="height:50px; margin-top:5px;">
                            <v-col cols="auto" style="margin-right:10px; margin-left:26px;">
                              <v-checkbox v-model="dialogOptions.item.starts" label="Starts" hide-details class="body-1" style="padding:0px; margin-top:14px;"></v-checkbox>
                            </v-col>
                            <v-col cols="3" style="margin-top:3px;">
                              <v-text-field :disabled="!dialogOptions.item.starts" solo v-model="dialogOptions.item.startsValue" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                            </v-col>
                            <v-col cols="auto" style="margin-left:10px;">
                              <v-checkbox :disabled="!dialogOptions.item.starts" v-model="dialogOptions.item.startsInterval" label="Interval" hide-details class="body-1" style="padding:0px; margin-top:14px;"></v-checkbox>
                            </v-col>
                            <v-col style="margin-top:3px; margin-left:10px;">
                              <v-text-field :disabled="!dialogOptions.item.startsInterval" solo v-model="dialogOptions.item.startsIntervalValue" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                            </v-col>
                            <v-col style="margin-top:3px; margin-left:10px;">
                              <v-select :disabled="!dialogOptions.item.startsInterval" solo v-model="dialogOptions.item.startsIntervalOptions" :items="interval" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                            </v-col>
                          </v-row>
                          <v-row no-gutters style="height:50px; margin-top:5px;">
                            <v-col cols="auto" style="margin-right:10px;">
                              <v-checkbox v-model="dialogOptions.item.ends" label="Ends" hide-details class="body-1" style="padding:0px; margin-top:14px; margin-left:26px; margin-right:9px;"></v-checkbox>
                            </v-col>
                            <v-col cols="3" style="margin-top:3px;">
                              <v-text-field :disabled="!dialogOptions.item.ends" solo v-model="dialogOptions.item.endsValue" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                            </v-col>
                            <v-col cols="auto" style="margin-left:10px;">
                              <v-checkbox :disabled="!dialogOptions.item.ends" v-model="dialogOptions.item.endsInterval" label="Interval" hide-details class="body-1" style="padding:0px; margin-top:14px;"></v-checkbox>
                            </v-col>
                            <v-col style="margin-top:3px; margin-left:10px;">
                              <v-text-field :disabled="!dialogOptions.item.endsInterval" solo v-model="dialogOptions.item.endsIntervalValue" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                            </v-col>
                            <v-col style="margin-top:3px; margin-left:10px;">
                              <v-select :disabled="!dialogOptions.item.endsInterval" solo v-model="dialogOptions.item.endsIntervalOptions" :items="interval" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                            </v-col>
                          </v-row>
                        </div>
                      </v-card-text>
                    </v-card>
                    <!-- <div style="margin-left:auto; margin-right:auto; height:40vh; width:100%">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div> -->
                  </div>
                  <div v-else-if="dialogOptions.mode == 'renameEvent'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current name" required style="padding-top:0px;"></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'duplicateEvent'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current name" required style="padding-top:0px;"></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
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
      // Event Interval
      interval: ['SECOND','MINUTE','HOUR','DAY','WEEK','MONTH','QUARTER','YEAR','MINUTE_SECOND','HOUR_SECOND','HOUR_MINUTE','DAY_SECOND','DAY_MINUTE','DAY_HOUR','YEAR_MONTH'],
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
      'tableItems',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('CLICK_CONTEXTMENU_EVENT', this.contextMenuClicked);
  },
  watch: {
    dialog (val) {
      if (!val) return
      if (this.dialogEditor == null && this.dialogOptions.mode == 'createEvent') this.initEditor()
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
  },
  methods: {
    initEditor() {
      return
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
        let placeholder = `/*
SELECT COUNT(*) INTO cities
FROM world.city
WHERE CountryCode = country;
*/`
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
      if (item == 'Create Event') this.createEvent()
      else if (item == 'Rename Event') this.renameEvent()
      else if (item == 'Duplicate Event') this.duplicateEvent()
      else if (item == 'Delete Event') this.deleteEvent()
      else if (item == 'Export') 1 == 1
      else if (item == 'Copy Event Syntax') this.copyEventSyntaxSubmit()
    },
    createEvent() {
      let dialogOptions = { 
        mode: 'createEvent', 
        title: 'Create Event', 
        text: '', 
        item: { name: '', timing: '0' }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      if (this.dialogEditor != null) this.dialogEditor.setValue('')
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    renameEvent() {
      let dialogOptions = { 
        mode: 'renameEvent', 
        title: 'Rename Event', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    duplicateEvent() {
      let dialogOptions = { 
        mode: 'duplicateEvent', 
        title: 'Duplicate Event', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Submit',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    deleteEvent() {
      let dialogOptions = { 
        mode: 'deleteEvent', 
        title: 'Delete Event?', 
        text: "Are you sure you want to delete the event '" + this.contextMenuItem.name + "'? This operation cannot be undone.",
        item: {}, 
        submit: 'Submit',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
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
      if (this.dialogOptions.mode == 'createEvent') this.createEventSubmit()
      else if (this.dialogOptions.mode == 'renameEvent') this.renameEventSubmit() 
      else if (this.dialogOptions.mode == 'duplicateEvent') this.duplicateEventSubmit() 
      else if (this.dialogOptions.mode == 'deleteEvent') this.deleteEventSubmit() 
    },
    createEventSubmit() {
      let eventName = this.dialogOptions.item.name
      let procedureParams = this.dialogOptions.item.params
      let procedureCode = this.dialogEditor.getValue().endsWith(';') ? this.dialogEditor.getValue() : this.dialogEditor.getValue() + ';'
      let procedureDeterministic = this.dialogOptions.item.deterministic ? '\nDETERMINISTIC' : ''
      let query = "CREATE EVENT " + eventName + ' (' + procedureParams + ')' + procedureDeterministic + '\nBEGIN\n' + procedureCode + '\nEND;'
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created proceure
          this.treeviewSelected = { id: 'event|' + eventName, name: eventName, type: 'Event' }
          this.treeview = ['event|' + eventName]
          // Open treeview parent
          this.treeviewOpened = ['events']
          // Change view to Info
          this.headerTab = 3
          this.headerTabSelected = 'info_event'
          EventBus.$emit('GET_INFO', 'event')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    renameEventSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE EVENT " + currentName, "DROP EVENT IF EXISTS " + currentName]
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Event'].split(' EVENT `' + currentName + '`')[1]
        let query = "CREATE EVENT " + newName + " " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.treeviewSelected = { id: 'event|' + newName, name: newName, type: 'Event' }
            this.treeview = ['event|' + newName]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_event'
            EventBus.$emit('GET_INFO', 'event')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    duplicateEventSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE EVENT " + currentName]
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Event'].split(' EVENT `' + currentName + '`')[1]
        let query = "CREATE EVENT " + newName + " " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.treeviewSelected = { id: 'event|' + newName, name: newName, type: 'Event' }
            this.treeview = ['event|' + newName]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_event'
            EventBus.$emit('GET_INFO', 'event')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    deleteEventSubmit() {
      let name = this.contextMenuItem.name
      let query = "DROP EVENT " + name + ";"
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Unselect deleted view
          this.treeviewSelected = {}
          this.treeview = []
          // Change view to Client
          this.headerTab = 0
          this.headerTabSelected = 'client'
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    copyEventSyntaxSubmit() {
      let name = this.contextMenuItem.name
      let query = "SHOW CREATE EVENT " + name + ";"
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Event']
        navigator.clipboard.writeText(syntax)
        EventBus.$emit('SEND_NOTIFICATION', "Syntax copied to clipboard", 'info')
      }).catch(() => {}).finally(() => { this.loading = false })
    },
  }
}
</script>