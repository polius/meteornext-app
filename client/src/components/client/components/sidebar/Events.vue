<template>
  <div>
    <!------------>
    <!-- EVENTS -->
    <!------------>
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
                  <div class="body-1">{{ dialogOptions.text }}</div>
                  <div v-if="dialogOptions.mode == 'createEvent'">
                    <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus :rules="[v => !!v || '']" required hide-details style="padding-top:8px"></v-text-field>
                    <v-radio-group v-model="dialogOptions.item.timing" hide-details style="margin-top:20px;">
                      <v-row no-gutters>
                        <v-col cols="auto">
                          <div class="text-subtitle-1 font-weight-regular" style="margin-right:15px;">SCHEDULE:</div>
                        </v-col>
                        <v-col cols="auto" style="margin-top:2px">
                          <v-radio label="One-time event" value="at"></v-radio>
                        </v-col>
                        <v-col cols="auto" style="margin-top:2px; margin-left:15px;">
                          <v-radio label="Recurring event" value="every"></v-radio>
                        </v-col>
                      </v-row>
                    </v-radio-group>
                    <div style="margin-top:15px">
                      <div v-if="dialogOptions.item.timing == 'at'">
                        <v-row no-gutters style="height:50px;">
                          <v-col cols="auto">
                            <div class="body-1" style="margin-top:14px">Execute at:</div>
                          </v-col>
                          <v-col cols="3" style="margin-top:2px; margin-left:10px">
                            <v-text-field @click="scheduleOpen('executedAt')" solo readonly v-model="dialogOptions.item.executedAt" :rules="[v => !!v || '']" required hide-details style="padding-top:0px;"></v-text-field>
                          </v-col>
                          <v-col cols="auto" style="margin-left:10px">
                            <v-checkbox @change="$nextTick(() => $refs.executedAtInterval.focus())" v-model="dialogOptions.item.executedAtInterval" label="Interval" hide-details class="body-1" style="padding:0px; margin-top:14px;"></v-checkbox>
                          </v-col>
                          <v-col style="margin-top:2px; margin-left:12px;">
                            <v-text-field ref="executedAtInterval" :disabled="!dialogOptions.item.executedAtInterval" solo v-model="dialogOptions.item.executeAtIntervalValue" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                          </v-col>
                          <v-col style="margin-top:2px; margin-left:10px;">
                            <v-select :disabled="!dialogOptions.item.executedAtInterval" solo v-model="dialogOptions.item.executeAtIntervalOption" :items="intervalItems" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
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
                          <v-col style="margin-top:2px; margin-left:10px;">
                            <v-select solo v-model="dialogOptions.item.executedEveryOption" :items="intervalItems" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                          </v-col>
                        </v-row>
                        <v-row no-gutters style="height:50px; margin-top:5px;">
                          <v-col cols="auto" style="margin-right:10px; margin-left:31px;">
                            <v-checkbox @click="dialogOptions.item.executedEveryStarts && dialogOptions.item.executedEveryStartsValue.length == 0 ? scheduleOpen('executedEveryStartsValue') : {}" @change="dialogOptions.item.executedEveryStartsInterval = false" v-model="dialogOptions.item.executedEveryStarts" label="Starts" hide-details class="body-1" style="padding:0px; margin-top:14px;"></v-checkbox>
                          </v-col>
                          <v-col cols="3" style="margin-top:2px;">
                            <v-text-field @click="scheduleOpen('executedEveryStartsValue')" :disabled="!dialogOptions.item.executedEveryStarts" solo v-model="dialogOptions.item.executedEveryStartsValue" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                          </v-col>
                          <v-col cols="auto" style="margin-left:10px;">
                            <v-checkbox @change="$nextTick(() => $refs.executedEveryStartsIntervalValue.focus())" :disabled="!dialogOptions.item.executedEveryStarts" v-model="dialogOptions.item.executedEveryStartsInterval" label="Interval" hide-details class="body-1" style="padding:0px; margin-top:14px;"></v-checkbox>
                          </v-col>
                          <v-col style="margin-top:2px; margin-left:12px;">
                            <v-text-field ref="executedEveryStartsIntervalValue" :disabled="!dialogOptions.item.executedEveryStartsInterval" solo v-model="dialogOptions.item.executedEveryStartsIntervalValue" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                          </v-col>
                          <v-col style="margin-top:2px; margin-left:10px;">
                            <v-select :disabled="!dialogOptions.item.executedEveryStartsInterval" solo v-model="dialogOptions.item.executedEveryStartsIntervalOption" :items="intervalItems" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                          </v-col>
                        </v-row>
                        <v-row no-gutters style="height:50px; margin-top:5px;">
                          <v-col cols="auto" style="margin-right:10px; margin-left:5px;">
                            <v-checkbox @click="dialogOptions.item.executedEveryEnds && dialogOptions.item.executedEveryEndsValue.length == 0 ? scheduleOpen('executedEveryEndsValue') : {}" @change="dialogOptions.item.executedEveryEndsInterval = false" v-model="dialogOptions.item.executedEveryEnds" label="Ends" hide-details class="body-1" style="padding:0px; margin-top:14px; margin-left:26px; margin-right:9px;"></v-checkbox>
                          </v-col>
                          <v-col cols="3" style="margin-top:2px;">
                            <v-text-field @click="scheduleOpen('executedEveryEndsValue')" :disabled="!dialogOptions.item.executedEveryEnds" solo v-model="dialogOptions.item.executedEveryEndsValue" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                          </v-col>
                          <v-col cols="auto" style="margin-left:10px;">
                            <v-checkbox @change="$nextTick(() => $refs.executedEveryEndsIntervalValue.focus())" :disabled="!dialogOptions.item.executedEveryEnds" v-model="dialogOptions.item.executedEveryEndsInterval" label="Interval" hide-details class="body-1" style="padding:0px; margin-top:14px;"></v-checkbox>
                          </v-col>
                          <v-col style="margin-top:2px; margin-left:12px;">
                            <v-text-field ref="executedEveryEndsIntervalValue" :disabled="!dialogOptions.item.executedEveryEndsInterval" solo v-model="dialogOptions.item.executedEveryEndsIntervalValue" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                          </v-col>
                          <v-col style="margin-top:2px; margin-left:10px;">
                            <v-select :disabled="!dialogOptions.item.executedEveryEndsInterval" solo v-model="dialogOptions.item.executedEveryEndsIntervalOption" :items="intervalItems" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                          </v-col>
                        </v-row>
                      </div>
                    </div>
                    <div style="margin-left:auto; margin-right:auto; margin-top:15px; height:30vh; width:100%">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
                    <v-select v-model="dialogOptions.item.onCompletion" label="On Completion" :items="['PRESERVE','NOT PRESERVE']" :rules="[v => !!v || '']" required hide-details style="margin-top:15px; padding-bottom:5px"></v-select>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'renameEvent'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current Name" required></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New Name" autofocus required hide-details style="padding-top:0px; padding-bottom:5px"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'duplicateEvent'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current Name" required></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New Name" autofocus required hide-details style="padding-top:0px; padding-bottom:5px"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'deleteEvent'">
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
    <!-------------->
    <!-- SCHEDULE -->
    <!-------------->
    <v-dialog v-model="scheduleDialog" persistent width="290px">
      <v-date-picker v-if="scheduleMode == 'date'" v-model="scheduleDate" color="info" scrollable>
        <v-btn text color="#00b16a" @click="scheduleSubmit()">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="scheduleClose()">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="scheduleNow()">Now</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="scheduleMode == 'time'" v-model="scheduleTime" color="info" format="24hr" use-seconds scrollable>
        <v-btn text color="#00b16a" @click="scheduleSubmit()">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="scheduleClose()">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="scheduleNow()">Now</v-btn>
      </v-time-picker>
    </v-dialog>
  </div>
</template>

<script>
import moment from 'moment'

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
      // Event Interval
      intervalItems: ['SECOND','MINUTE','HOUR','DAY','WEEK','MONTH','QUARTER','YEAR','MINUTE_SECOND','HOUR_SECOND','HOUR_MINUTE','DAY_SECOND','DAY_MINUTE','DAY_HOUR','YEAR_MONTH'],
      // Schedule
      scheduleDialog: false,
      scheduleMode: 'date',
      scheduleDate: '',
      scheduleTime: '',
      scheduleComponent: '',
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
    EventBus.$on('click-contextmenu-event', this.contextMenuClicked);
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
      if (!val) return
      if (this.dialogEditor == null && this.dialogOptions.mode == 'createEvent') this.initEditor()
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
  },
  methods: {
    tst() {
      this.$nextTick(() => this.$refs.gogo.focus())
    },
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
      if (item == 'Create Event') this.createEvent()
      else if (item == 'Rename Event') this.renameEvent()
      else if (item == 'Duplicate Event') this.duplicateEvent()
      else if (item == 'Delete Event') this.deleteEvent()
      else if (item == 'Export') this.exportEvent()
      else if (item == 'Copy Event Syntax') this.copyEventSyntaxSubmit()
    },
    createEvent() {
      let dialogOptions = { 
        mode: 'createEvent',
        icon: 'fas fa-plus', 
        title: 'CREATE EVENT', 
        text: '', 
        item: { 
          name: '',
          timing: 'at',
          executedAt: '', executedAtInterval: false, executeAtIntervalValue: '', executeAtIntervalOption: '',
          executedEvery: '', executedEveryOption: '',
          executedEveryStarts: '', executedEveryStartsValue: '', executedEveryStartsInterval: false, executedEveryStartsIntervalValue: '', executedEveryStartsIntervalOption: '',
          executedEveryEnds: '', executedEveryEndsValue: '', executedEveryEndsInterval: false, executedEveryEndsIntervalValue: '', executedEveryEndsIntervalOption: '',
          onCompletion: 'NOT PRESERVE'
        }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      if (this.dialogEditor != null) this.dialogEditor.setValue('')
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    renameEvent() {
      let dialogOptions = { 
        mode: 'renameEvent', 
        icon: 'fas fa-feather-alt',
        title: 'RENAME EVENT', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    duplicateEvent() {
      let dialogOptions = { 
        mode: 'duplicateEvent',
        icon: 'fas fa-clone', 
        title: 'DUPLICATE EVENT', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    deleteEvent() {
      let dialogOptions = { 
        mode: 'deleteEvent',
        icon: 'fas fa-minus', 
        title: 'DELETE EVENT', 
        text: "Are you sure you want to delete the selected events? This operation cannot be undone.",
        item: {}, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    exportEvent() {
      const items = this.sidebarSelected.map(x => x.name)
      EventBus.$emit('show-bottombar-objects-export', { object: 'events', items })
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
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
      let eventCode = this.dialogEditor.getValue().endsWith(';') ? this.dialogEditor.getValue() : this.dialogEditor.getValue() + ';'
      let query = "CREATE EVENT `" + eventName + '` ON SCHEDULE'

      if (this.dialogOptions.item.timing == 'at') {
        query += "\nAT '" + this.dialogOptions.item.executedAt + "'"
        if (this.dialogOptions.item.executedAtInterval) query += ' + INTERVAL ' + this.dialogOptions.item.executeAtIntervalValue + ' ' + this.dialogOptions.item.executeAtIntervalOption
      }
      else if (this.dialogOptions.item.timing == 'every') {
        query += '\nEVERY ' + this.dialogOptions.item.executedEvery + ' ' + this.dialogOptions.item.executedEveryOption
        if (this.dialogOptions.item.executedEveryStartsInterval) {
          query += "\nSTARTS '" + this.dialogOptions.item.executedEveryStartsValue + "'"
          if (this.dialogOptions.item.executedEveryStartsInterval) query += " + INTERVAL " + this.dialogOptions.item.executedEveryStartsIntervalValue + ' ' + this.dialogOptions.item.executedEveryStartsIntervalOption
        }
        if (this.dialogOptions.item.executedEveryEndsInterval) {
          query += "\nENDS '" + this.dialogOptions.item.executedEveryEndsValue + "'"
          if (this.dialogOptions.item.executedEveryEndsInterval) query += " + INTERVAL " + this.dialogOptions.item.executedEveryEndsIntervalValue + ' ' + this.dialogOptions.item.executedEveryEndsIntervalOption
        }
      }
      query += "\nON COMPLETION " + this.dialogOptions.item.onCompletion
      query += '\nDO\nBEGIN\n' + eventCode + '\nEND;'

      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created proceure
          this.sidebarSelected = [{ id: 'event|' + eventName, name: eventName, type: 'Event' }]
          // Open sidebar parent
          this.sidebarOpened = ['events']
          // Change view to Info
          this.headerTab = 3
          this.headerTabSelected = 'info_event'
          EventBus.$emit('get-info', 'event')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    renameEventSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE EVENT `" + currentName + "`", "DROP EVENT IF EXISTS `" + currentName + "`"]
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Event'].split(' EVENT `' + currentName + '`')[1]
        let query = "CREATE EVENT `" + newName + "`" + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('execute-sidebar', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = [{ id: 'event|' + newName, name: newName, type: 'Event' }]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_event'
            EventBus.$emit('get-info', 'event')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    duplicateEventSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE EVENT `" + currentName + "`"]
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Event'].split(' EVENT `' + currentName + '`')[1]
        let query = "CREATE EVENT `" + newName + "` " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('execute-sidebar', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = [{ id: 'event|' + newName, name: newName, type: 'Event' }]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_event'
            EventBus.$emit('get-info', 'event')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    deleteEventSubmit() {
      let queries = []
      for (let item of this.sidebarSelected) queries.push("DROP EVENT `" + item.name + "`;")
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
    copyEventSyntaxSubmit() {
      let name = this.contextMenuItem.name
      let query = "SHOW CREATE EVENT `" + name + "`;"
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Event'] + ';'
        navigator.clipboard.writeText(syntax)
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    // SCHEDULE
    scheduleOpen(component) {
      this.scheduleComponent = component
      if (this.dialogOptions.item[component] == '') {
        const date = moment()
        this.scheduleDate = date.format("YYYY-MM-DD")
        this.scheduleTime = date.format("HH:mm:ss")
      }
      this.scheduleDialog = true
    },
    scheduleClose() {
      if (this.dialogOptions.item.executedEveryStarts && this.dialogOptions.item.executedEveryStartsValue.length == 0) this.dialogOptions.item.executedEveryStarts = false
      else if (this.dialogOptions.item.executedEveryEnds && this.dialogOptions.item.executedEveryEndsValue.length == 0) this.dialogOptions.item.executedEveryEnds = false
      this.scheduleDialog = false
      this.scheduleMode = 'date'
    },
    scheduleNow() {
      const date = moment()
      if (this.scheduleMode == 'date') this.scheduleDate = date.format("YYYY-MM-DD")
      else if (this.scheduleMode == 'time') this.scheduleTime = date.format("HH:mm:ss")
    },
    scheduleSubmit() {
      if (this.scheduleMode == 'date') this.scheduleMode = 'time'
      else if (this.scheduleMode == 'time') {
        this.dialogOptions.item[this.scheduleComponent] = this.scheduleDate + ' ' + this.scheduleTime
        this.scheduleMode = 'date'
        this.scheduleDialog = false
      }
    },
  }
}
</script>