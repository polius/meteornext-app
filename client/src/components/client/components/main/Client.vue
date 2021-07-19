<template>
  <div style="height:100%">
    <!------------>
    <!-- CLIENT -->
    <!------------>
    <div style="height:calc(100% - 36px)">
      <Splitpanes horizontal @ready="initAceClient()">
        <Pane size="50">
          <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
            <div id="editor" style="float:left"></div>
          </div>
        </Pane>
        <Pane size="50" min-size="0">
          <ag-grid-vue ref="agGridClient" suppressContextMenu preventDefaultOnContextMenu oncontextmenu="return false" @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" @row-clicked="onRowClicked" @cell-context-menu="onContextMenu" @row-data-changed="onRowDataChanged" @cell-editing-started="cellEditingStarted" @cell-editing-stopped="cellEditingStopped" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :stopEditingWhenGridLosesFocus="true" :columnDefs="clientHeaders" :rowData="clientItems"></ag-grid-vue>
          <v-menu v-model="contextMenu" :position-x="contextMenuX" :position-y="contextMenuY" absolute offset-y style="z-index:10">
            <v-list style="padding:0px;">
              <v-list-item-group v-model="contextMenuModel">
                <div v-for="[index, item] of contextMenuItems.entries()" :key="index">
                  <v-list-item v-if="item != '|'" @click="contextMenuClicked(item)">
                    <v-list-item-title>{{item}}</v-list-item-title>
                  </v-list-item>
                  <v-divider v-else></v-divider>
                </div>
              </v-list-item-group>
            </v-list>
          </v-menu>
        </Pane>
      </Splitpanes>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn :disabled="clientItems.length == 0" @click="exportRows" text small title="Export rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-arrow-down</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn :disabled="clientItems.length == 0" @click="compressColumns" text small title="Compress columns" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-compress</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn :disabled="clientItems.length == 0" @click="expandColumns" text small title="Expand columns" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-expand</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBar.client['status']=='executing'" title="Executing" small style="color:rgb(250, 130, 49); padding-bottom:1px; padding-right:7px;">fas fa-spinner</v-icon>
            <v-icon v-else-if="bottomBar.client['status']=='success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:7px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBar.client['status']=='failure'" title="Failed" small style="color:#EF5354; padding-bottom:1px; padding-right:7px;">fas fa-times-circle</v-icon>
            <v-icon v-else-if="bottomBar.client['status']=='stopped'" title="Stopped" small style="color:#EF5354; padding-bottom:1px; padding-right:7px;">fas fa-exclamation-circle</v-icon>
            <span :title="bottomBar.client['text']">{{ bottomBar.client['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBar.client['info'] }}</div>
        </v-col>
      </v-row>
    </div>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" :persistent="dialogMode == 'cellEditingError'" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; padding-bottom:3px">{{ dialogIcon }}</v-icon>{{ dialogTitle }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn v-if="!(['error','cellEditingError'].includes(dialogMode))" :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form">
                  <div v-if="dialogText.length>0" class="body-1">{{ dialogText }}</div>
                  <v-select v-if="dialogMode=='export'" filled v-model="dialogSelect" :items="['SQL','CSV','JSON','Meteor']" label="Format" hide-details></v-select>
                </v-form>
                <div v-if="dialogSubmitText.length > 0 || dialogCancelText.length > 0">
                  <v-divider style="margin-top:15px"></v-divider>
                  <v-row no-gutters style="margin-top:15px">
                    <v-col v-if="dialogSubmitText.length > 0" cols="auto" style="margin-right:5px">
                      <v-btn :loading="loading" @click="dialogSubmit" :color="dialogSubmitText == 'Close' ? 'primary' : '#00b16a'">{{ dialogSubmitText }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogCancelText.length > 0">
                      <v-btn :disabled="loading" @click="dialogCancel" color="#EF5354">{{ dialogCancelText }}</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------------->
    <!-- DIALOG: EDIT CONTENT -->
    <!-------------------------->
    <v-dialog v-model="editDialog" persistent max-width="80%">
      <v-card>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-row no-gutters>
                <v-col class="flex-grow-1 flex-shrink-1">
                  <div class="text-h6 white--text" style="font-weight:400; font-size:1.1rem!important; margin-top:3px; margin-left:1px;">{{ editDialogTitle }}</div>
                </v-col>
                <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="margin-right:20px">
                  <v-checkbox @change="editDialogWrapChange" v-model="editDialogWrap" label="Wrap text" hide-details style="margin-top:5px"></v-checkbox>
                </v-col>
                <v-col v-if="editDialogFormat == 'JSON'" cols="auto" class="flex-grow-0 flex-shrink-0" style="margin-right:10px">
                  <v-btn @click="editDialogParse" hide-details style="margin-top:2px">Parse</v-btn>
                </v-col>
                <v-col v-if="editDialogFormat == 'JSON'" cols="auto" class="flex-grow-0 flex-shrink-0" style="margin-right:15px">
                  <v-btn @click="editDialogValidate(true)" hide-details style="margin-top:2px">Validate</v-btn>
                </v-col>
                <v-col cols="2" class="flex-grow-0 flex-shrink-0">
                  <v-select @change="editDialogApplyFormat" v-model="editDialogFormat" :items="editDialogFormatItems" label="Format" outlined dense hide-details></v-select>
                </v-col>
              </v-row>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:15px">
                  <div style="margin-left:auto; margin-right:auto; height:70vh; width:100%">
                    <div id="editDialogEditor" style="height:100%;"></div>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px">
                      <v-btn @click="editDialogSubmit" color="#00b16a">Save</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn @click="editDialogCancel" color="#EF5354">Cancel</v-btn>
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

<style scoped>
::v-deep .v-list-item__title {
  font-size: 0.9rem;
}
::v-deep .v-list-item__content {
  padding:0px;
}
::v-deep .v-list-item {
  min-height:40px;
}
</style>

<script>
import axios from 'axios'

import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import ace from "ace-builds"
import 'ace-builds/webpack-resolver'
import 'ace-builds/src-noconflict/ext-language_tools'

import {AgGridVue} from "ag-grid-vue";
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import sqlFormatter from '@sqltools/formatter'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // AG Grid
      currentCellEditNode: {},
      currentCellEditValues: {},
      currentQueryMetadata: { database: null, table: null},
      // Dialog
      dialog: false,
      dialogMode: '',
      dialogIcon: '',
      dialogTitle: '',
      dialogText: '',
      dialogSubmitText: '',
      dialogCancelText: '',
      // Dialog - Content Edit
      editDialog: false,
      editDialogTitle: '',
      editDialogFormat: 'Text',
      editDialogFormatItems: ['Text','JSON','Python'],
      editDialogWrap: false,
      editDialogValue: '',
      editDialogEditor: null,
      // Context Menu
      contextMenu: false,
      contextMenuModel: null,
      contextMenuItems: ['Copy SQL','Copy CSV','Copy JSON','|','Select All','Deselect All'],
      contextMenuItem: {},
      contextMenuX: 0,
      contextMenuY: 0,
    }
  },
  components: { Splitpanes, Pane, AgGridVue },
  mounted () {
    EventBus.$on('run-query', this.runQuery);
    EventBus.$on('explain-query', this.explainQuery);
    EventBus.$on('stop-query', this.stopQuery);
    EventBus.$on('beautify-query', this.beautifyQuery);
    EventBus.$on('minify-query', this.minifyQuery);
    EventBus.$on('select-favourite', this.selectFavourite);
  },
  computed: {
    ...mapFields([
      'index',
      'id',
      'headerTabSelected',
      'clientHeaders',
      'clientItems',
      'clientQueries',
      'clientCursor',
      'clientRange',
      'clientQuery',
      'clientQueryStopped',
      'bottomBar',
      'server',
      'clientExecuting',
      'database',
      'sidebarMode',
      'clientCompleters',
      'clientSession',
    ], { path: 'client/connection' }),
    ...mapFields([
      'editor',
      'editorMarkers',
      'editorTools',
      'editorKeywords',
      'gridApi',
      'columnApi',
    ], { path: 'client/components' }),
    ...mapFields([
      'currentConn',
      'connections',
      'settings',
      'dialogOpened',
    ], { path: 'client/client' }),
  },
  watch: {
    sidebarMode(val) {
      if (val == 'objects') this.editor.setValue(this.clientQueries, 1)
    },
    currentConn() {
      // Reload Table Headers
      const headers = this.clientHeaders
      this.gridApi.client.setColumnDefs([])
      this.clientHeaders = headers
      // Discard any previous table modifications
      this.cellEditingDiscard()
      // Load Current Connnection Editor
      if (this.clientSession == null) {
        this.clientSession = ace.createEditSession('', 'ace/mode/mysql')
        this.editor.setSession(this.clientSession)
      }
      else this.editor.setSession(this.clientSession)
      this.editor.setValue(this.clientQueries, 1)
      if (this.clientCursor != null && this.clientRange != null) {
        this.editor.moveCursorTo(this.clientCursor.row, this.clientCursor.column)
        let reverse = (this.clientCursor.row == this.clientRange.start.row && this.clientCursor.column == this.clientRange.start.column)
        this.editor.selection.setSelectionRange(this.clientRange, reverse)
      }
      if (this.headerTabSelected == 'client' && this.sidebarMode == 'objects') this.editor.focus()
    },
    dialog: function(val) {
      this.dialogOpened = val
      if (!val) this.editor.focus()
    },
    headerTabSelected(newValue, oldValue) {
      if (newValue == 'client') {
        this.editor.setValue(this.clientQueries, 1)
        if (this.clientCursor != null && this.clientRange != null) {
          this.editor.moveCursorTo(this.clientCursor.row, this.clientCursor.column)
          let reverse = (this.clientCursor.row == this.clientRange.start.row && this.clientCursor.column == this.clientRange.start.column)
          this.editor.selection.setSelectionRange(this.clientRange, reverse)
        }
        if (this.database != null && this.database.length > 0) this.editor.focus()
      }
      else if (oldValue == 'client') {
        this.clientQueries = this.editor.getValue()
        this.clientCursor = this.editor.getCursorPosition()
        this.clientRange = this.editor.selection.getRange()
      }
    },
  },
  methods: {
    onGridReady(params) {
      this.gridApi.client = params.api
      this.columnApi.client = params.columnApi
      this.$refs['agGridClient'].$el.addEventListener('click', this.onGridClick)
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.client.deselectAll()
        // this.cellEditingSubmit(this.currentCellEditNode, this.currentCellEditValues)
        this.cellEditConfirm()
      }
    },
    onRowClicked(event) {
      if (Object.keys(this.currentCellEditNode).length != 0 && this.currentCellEditNode.rowIndex != event.rowIndex) {
        // this.cellEditingSubmit(this.currentCellEditNode, this.currentCellEditValues)
        this.cellEditConfirm()
      }
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        let selectedRows = this.gridApi.client.getSelectedRows()
        if (selectedRows.length > 1) {
          // Copy values
          let header = Object.keys(selectedRows[0])
          let value = selectedRows.map(row => header.map(fieldName => row[fieldName] == null ? 'NULL' : row[fieldName]).join('\t')).join('\n')
          navigator.clipboard.writeText(value)
          // Apply effect
          // this.gridApi.client.flashCells({
          //   rowNodes: this.gridApi.client.getSelectedNodes(),
          //   flashDelay: 200,
          //   fadeDelay: 200,
          // })
        }
        else {
          // Copy value
          navigator.clipboard.writeText(e.value)
          // Apply effect
          this.gridApi.client.flashCells({
            rowNodes: this.gridApi.client.getSelectedNodes(),
            columns: [this.gridApi.client.getFocusedCell().column.colId],
            flashDelay: 200,
            fadeDelay: 200,
          })
        }
      }
      else if (e.event.key == 'Enter') {
        // this.cellEditingSubmit(this.currentCellEditNode, this.currentCellEditValues)
        this.cellEditConfirm()
      }
      else if (['ArrowUp','ArrowDown'].includes(e.event.key)) {
        let cell = this.gridApi.client.getFocusedCell()
        let row = this.gridApi.client.getDisplayedRowAtIndex(cell.rowIndex)
        let node = this.gridApi.client.getRowNode(row.id)
        this.gridApi.client.deselectAll()
        node.setSelected(true)
      }
      else if (e.event.key == 'a' && (e.event.ctrlKey || e.event.metaKey)) {
        this.gridApi.client.selectAll()
      }
    },
    getCurrentPKs(resolve, reject) {
      const payload = { 
        connection: this.id + '-shared',
        server: this.server.id,
        ...this.currentQueryMetadata
      }
      axios.get('/client/pks', { params: payload })
      .then((response) => {
        resolve(response.data.pks)
      })
      .catch((error) => {
        if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        reject()
      })
    },
    cellEditingStarted(event) {
      this.$nextTick(() => {
        // Store row node
        this.currentCellEditNode = this.gridApi.client.getSelectedNodes()[0]
      
        // Store row values
        if (Object.keys(this.currentCellEditValues).length == 0) {
          let node = this.gridApi.client.getSelectedNodes()[0].data
          let keys = Object.keys(node)
          this.currentCellEditValues = {}
          for (let i = 0; i < keys.length; ++i) {
            this.currentCellEditValues[keys[i]] = {'old': node[keys[i]] == 'NULL' ? null : node[keys[i]]}
          }
        }
        // If the cell includes an special character (\n or \t) or the value length >= 50 chars, ... then open the extended editor
        if (event.value.toString().length >= 50 || (event.value.toString().match(/\n/g)||[]).length > 0 || (event.value.toString().match(/\t/g)||[]).length > 0) {
          if (this.editDialogEditor != null && this.editDialogEditor.getValue().length > 0) this.editDialogEditor.setValue('')
          else this.editDialogOpen(event.colDef.headerName, event.value.toString())
        }
      })
    },
    cellEditingStopped(event) {
      // Store new value
      if (event.value == 'NULL') this.currentCellEditNode.setDataValue(event.colDef.field, null)
      if (this.currentCellEditValues[event.colDef.field] !== undefined) this.currentCellEditValues[event.colDef.field]['new'] = event.value == 'NULL' ? null : event.value
    },
    cellEditingSubmit(node, values) {
      if (Object.keys(values).length == 0) return
      new Promise((resolve, reject) => this.getCurrentPKs(resolve, reject)).then((pks) => {
        // Build values to update
        var valuesToUpdate = []
        let keys = Object.keys(values)
        for (let i = 0; i < keys.length; ++i) {
          if (values[keys[i]]['old'] != values[keys[i]]['new']) {
            if (values[keys[i]]['new'] !== undefined) {
              if (values[keys[i]]['new'] == null) valuesToUpdate.push('`' + keys[i] + "` = NULL")
              else valuesToUpdate.push('`' + keys[i] + "` = " + JSON.stringify(values[keys[i]]['new']))
            }
          }
        }
        if (valuesToUpdate.length > 0) {
          // Check if PKs exists in the result set
          if (pks.length == 0 || !pks.every(x => x in values)) {
            let dialogOptions = {
              'mode': 'cellEditingError',
              'icon': 'fas fa-exclamation-triangle',
              'title': 'ERROR',
              'text': pks.length == 0 ? "The table '" + this.currentQueryMetadata.table + "' does not contain a primary key constraint." : "The result set does not contain the primary keys. Please include the PK columns: " + pks.join(','),
              'button1': 'Edit row',
              'button2': 'Discard changes'
            }
            this.showDialog(dialogOptions)
            return
          }
          // Build Query
          let where = pks.map(x => '`' + x + '` = ' + JSON.stringify(values[x]['old']))
          let query = "UPDATE `" + this.currentQueryMetadata.database + "`.`" + this.currentQueryMetadata.table + "` SET " + valuesToUpdate.join(', ') + " WHERE " + where.join(' AND ') + ';'
          // Execute Query
          const payload = {
            connection: this.id + '-shared',
            server: this.server.id,
            database: this.database,
            queries: [query]
          }
          const server = this.server
          const index = this.index
          this.gridApi.client.showLoadingOverlay()
          axios.post('/client/execute', payload)
            .then((response) => {
              let current = this.connections.find(c => c['index'] == index)
              if (current === undefined) return
              this.gridApi.client.hideOverlay()
              let data = JSON.parse(response.data.data)
              // Build BottomBar
              this.parseClientBottomBar(data, current)
              // Add execution to history
              const history = { section: 'client', server: server, queries: data } 
              this.$store.dispatch('client/addHistory', history)
              // Clean vars
              this.currentCellEditNode = {}
              this.currentCellEditValues = {}
            })
            .catch((error) => {
              this.gridApi.client.hideOverlay()
              let current = this.connections.find(c => c['index'] == index)
              if (current === undefined) return
              if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
              else {
                // Show error
                let data = JSON.parse(error.response.data.data)
                let dialogOptions = {
                  'mode': 'cellEditingError',
                  'icon': 'fas fa-exclamation-triangle',
                  'title': 'ERROR',
                  'text': data.find(x => 'error' in x).error,
                  'button1': 'Edit row',
                  'button2': 'Discard changes'
                }
                this.showDialog(dialogOptions)
                // Build BottomBar
                this.parseClientBottomBar(data, current)
                // Restore vars
                this.currentCellEditNode = node
                this.currentCellEditValues = values
                // Add execution to history
                const history = { section: 'client', server: server, queries: data } 
                this.$store.dispatch('client/addHistory', history)
              }
            })
        }
        else {
          // Clean vars
          this.currentCellEditNode = {}
          this.currentCellEditValues = {}
        }
      })
    },
    editDialogOpen(title, text) {
      this.editDialogTitle = title
      this.editDialog = true
      if (this.editDialogEditor == null) {
        this.$nextTick(() => {
          this.editDialogEditor = ace.edit("editDialogEditor", {
            mode: "ace/mode/text",
            theme: "ace/theme/monokai",
            keyboardHandler: "ace/keyboard/vscode",
            fontSize: 14,
            showPrintMargin: false,
            wrap: false,
            indentedSoftWrap: false,
            showLineNumbers: true,
            scrollPastEnd: true
          })
          this.editDialogEditor.container.addEventListener("keydown", (e) => {
            // - Increase Font Size -
            if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
              let size = parseInt(this.editDialogEditor.getFontSize(), 10) || 12
              this.editDialogEditor.setFontSize(size + 1)
              e.preventDefault()
            }
            // - Decrease Font Size -
            else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
              let size = parseInt(this.editDialogEditor.getFontSize(), 10) || 12
              this.editDialogEditor.setFontSize(Math.max(size - 1 || 1))
              e.preventDefault()
            }
          }, false);
        })
      }
      this.$nextTick(() => {
        this.editDialogEditor.focus()
        this.editDialogEditor.setValue(text, 1)
        this.editDialogDetectFormat()
      })
    },
    editDialogWrapChange(val) {
      this.editDialogEditor.getSession().setUseWrapMode(val)
    },
    editDialogDetectFormat() {
      // Detect JSON and parse it
      try {
        let parsed = JSON.parse(this.editDialogEditor.getValue())
        this.editDialogEditor.session.setMode("ace/mode/json")
        this.editDialogEditor.session.setTabSize(2)
        this.editDialogEditor.setValue(JSON.stringify(parsed, null, '\t'), 1)
        this.editDialogFormat = 'JSON'
      } catch { 
        this.editDialogFormat = 'Text'
        this.editDialogEditor.session.setTabSize(4)
        this.editDialogEditor.session.setMode("ace/mode/text")
      }
    },
    editDialogApplyFormat(val) {
      this.editDialogEditor.session.setMode("ace/mode/" + val.toLowerCase())
      if (val == 'JSON') {
        try {
          let parsed = JSON.parse(this.editDialogEditor.getValue())
          this.editDialogEditor.session.setTabSize(2)
          this.editDialogEditor.setValue(JSON.stringify(parsed, null, '\t'), 1)
        } catch { 1==1 }
      }
      else {
        try {
          let parsed = JSON.parse(this.editDialogEditor.getValue())
          this.editDialogEditor.session.setTabSize(4)
          this.editDialogEditor.setValue(JSON.stringify(parsed), 1)
        } catch { 1==1 }
      }
    },
    editDialogValidate(notification) {
      try {
        JSON.parse(this.editDialogEditor.getValue())
        if (notification) EventBus.$emit('send-notification', 'JSON Validated!', '#00b16a', 2)
        return true
      } catch (error) {
        var dialogOptions = {
          'mode': 'info',
          'icon': 'fas fa-exclamation-triangle',
          'title': 'JSON NOT VALIDATED',
          'text': error.toString(),
          'button1': 'Close',
          'button2': ''
        }
        this.showDialog(dialogOptions)
        return false
      }
    },
    editDialogParse() {
      try {
        let parsed = JSON.parse(this.editDialogEditor.getValue())
        this.editDialogEditor.setValue(JSON.stringify(parsed, null, '\t'), 1)
      } catch (error) {
        var dialogOptions = {
          'mode': 'info',
          'icon': 'fas fa-exclamation-triangle',
          'title': 'JSON NOT VALIDATED',
          'text': error.toString(),
          'button1': 'Close',
          'button2': ''
        }
        this.showDialog(dialogOptions)
      }
    },
    editDialogSubmit() {
      if (this.editDialogFormat == 'JSON' && !this.editDialogValidate(false)) return
      let value = this.editDialogEditor.getValue()
      try { value = JSON.stringify(JSON.parse(value)) } catch { 1==1 }
      this.editDialog = false
      let nodes = this.gridApi.client.getSelectedNodes()
      for (let i = 0; i < nodes.length; ++i) nodes[i].setSelected(false)
      let focusedCell = this.gridApi.client.getFocusedCell()
      let currentNode = this.gridApi.client.getDisplayedRowAtIndex(focusedCell.rowIndex)
      currentNode.setSelected(true)
      currentNode.setDataValue(focusedCell.column.colId, value)
      this.$nextTick(() => {
        this.gridApi.client.startEditingCell({
          rowIndex: focusedCell.rowIndex,
          colKey: focusedCell.column.colId
        })
      })
    },
    editDialogCancel() {
      this.editDialog = false
      this.editDialogEditor.setValue('')
    },
    cellEditingDiscard() {
      // Close Dialog
      this.dialog = false
      // Restore Values
      const diff = Object.keys(this.currentCellEditValues).filter(x => 'new' in this.currentCellEditValues[x]).reduce((acc,val) => { acc[val] = this.currentCellEditValues[val]['old']; return acc; },{})
      for (const [k,v] of Object.entries(diff)) this.currentCellEditNode.setDataValue(k, v)
      // Clean Vars
      this.currentCellEditNode = {}
      this.currentCellEditValues = {}
    },
    cellEditingEdit() {
      // Close Dialog
      this.dialog = false
      // Edit Row
      setTimeout(() => {
        let focused = this.gridApi.client.getFocusedCell()
        this.currentCellEditNode.setSelected(true)
        this.gridApi.client.setFocusedCell(focused.rowIndex, focused.column.colId)
        this.gridApi.client.startEditingCell({
          rowIndex: focused.rowIndex,
          colKey: focused.column.colId
        });
      }, 100)
    },
    cellEditConfirm() {
      this.cellEditingSubmit(this.currentCellEditNode, this.currentCellEditValues)
      // var dialogOptions = {
      //   'mode': 'cellEdit',
      //   'title': 'Confirmation',
      //   'text': 'Want to confirm these changes?',
      //   'button1': 'Confirm',
      //   'button2': 'Cancel'
      // }
      // this.showDialog(dialogOptions)
    },
    cellEditConfirmSubmit() {
      this.cellEditingSubmit(this.currentCellEditNode, this.currentCellEditValues)
    },
    onContextMenu(e) {
      if (!this.gridApi.client.getSelectedNodes().some(x => x.id == e.node.id)) this.gridApi.client.deselectAll()
      e.node.setSelected(true)
      this.contextMenuModel = null
      this.contextMenuX = e.event.clientX
      this.contextMenuY = e.event.clientY
      this.contextMenu = true
    },
    contextMenuClicked(item) {
      if (item == 'Copy SQL') this.copySQL()
      else if (item == 'Copy CSV') this.copyCSV()
      else if (item == 'Copy JSON') this.copyJSON()
      else if (item == 'Select All') this.gridApi.client.selectAll()
      else if (item == 'Deselect All') this.gridApi.client.deselectAll()
    },
    copySQL() {
      var SqlString = require('sqlstring');
      let selectedRows = this.gridApi.client.getSelectedRows()
      let rawQuery = 'INSERT INTO `<table>` (' + Object.keys(selectedRows[0]).map(x => '`' + x.trim() + '`').join() + ')\nVALUES\n'
      let values = ''
      let args = []
      for (let row of selectedRows) {
        let rowVal = Object.values(row)
        args = [...args, ...rowVal];
        values += '(' + '?,'.repeat(rowVal.length).slice(0, -1) + '),\n'
      }
      rawQuery += values.slice(0,-2) + ';'
      let query = SqlString.format(rawQuery, args)
      navigator.clipboard.writeText(query)
    },
    copyCSV() {
      let selectedRows = this.gridApi.client.getSelectedRows()
      let replacer = (key, value) => value === null ? undefined : value
      let header = Object.keys(selectedRows[0])
      let csv = selectedRows.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
      csv.unshift(header.join(','))
      csv = csv.join('\r\n')
      navigator.clipboard.writeText(csv)
    },
    copyJSON() {
      let selectedRows = this.gridApi.client.getSelectedRows()
      let json = JSON.stringify(selectedRows)
      navigator.clipboard.writeText(json)
    },
    initAceClient() {
      // Editor Settings
      this.editor = ace.edit("editor", {
        mode: "ace/mode/mysql",
        theme: "ace/theme/monokai",
        keyboardHandler: "ace/keyboard/vscode",
        fontSize: parseInt(this.settings['font_size']) || 14,
        showPrintMargin: false,
        wrap: false,
        autoScrollEditorIntoView: true,
        enableBasicAutocompletion: true,
        enableLiveAutocompletion: true,
        enableSnippets: false,
        highlightActiveLine: false,
        scrollPastEnd: true
      });
      this.editor.session.setOptions({ tabSize: 4, useSoftTabs: false })

      // Highlight Queries
      this.editor.on("changeSelection", this.highlightQueries)

      // Add custom keybinds
      this.editor.commands.removeCommand('transposeletters')
      this.editor.commands.removeCommand('showSettingsMenu')
      this.editor.container.addEventListener("keydown", (e) => {
        // - Run Query/ies -
        if (e.key.toLowerCase() == "r" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          if (Object.keys(this.server).length > 0 && this.clientQuery['query'].length > 0) this.runQuery()
        }
        // - Explain Query/ies -
        else if (e.key.toLowerCase() == "e" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          if (Object.keys(this.server).length > 0 && this.clientQuery['query'].length > 0) this.explainQuery()
        }
        // - Beautify Query -
        else if (e.key.toLowerCase() == "b" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          if (Object.keys(this.server).length > 0 && this.clientQuery['query'].length > 0) this.beautifyQuery()
        }
        // - Minify Query -
        else if (e.key.toLowerCase() == "m" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          if (Object.keys(this.server).length > 0 && this.clientQuery['query'].length > 0) this.minifyQuery()
        }
        // - Increase Font Size -
        else if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          let size = parseInt(this.editor.getFontSize(), 10) || 12
          this.editor.setFontSize(size + 1)
        }
        // - Decrease Font Size -
        else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          let size = parseInt(this.editor.getFontSize(), 10) || 12
          this.editor.setFontSize(Math.max(size - 1 || 1))
        }
        // - Save Editor Queries -
        else if (e.key.toLowerCase() == "s" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          this.download('editor.txt', this.editor.getValue())
        }
        // - Add Comments -
        else if (e.key.toLowerCase() == "c" && (e.ctrlKey || e.metaKey) && e.shiftKey) {
          e.preventDefault()
          this.editor.execCommand('togglecomment')
        }
        // - Disable Default Browser Behaviour -
        else if (e.key.toLowerCase() == "," && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
        }
      }, false);

      // Convert Completer Keywords to Uppercase
      const keywords = {
        getCompletions(editor, session, pos, prefix, callback) {
          if (session.$mode.completer) {
            return session.$mode.completer.getCompletions(editor, session, pos, prefix, callback)
          }
          const state = editor.session.getState(pos.row)
          let completion = session.$mode.getCompletions(state, session, pos, prefix)
          completion = completion.map((obj) => {
            obj.value = obj.value.toUpperCase()
            obj.meta = obj.meta.charAt(0).toUpperCase() + obj.meta.slice(1)
            return obj
          })
          return callback(null, completion)
        },
      }
      this.editorKeywords = keywords
      this.editor.completers = [keywords]

      // Init Autocompleter
      var Autocomplete = ace.require("ace/autocomplete").Autocomplete
      this.editor.completer = new Autocomplete()
      this.editor.completer.editor = this.editor
      this.editor.completer.$init()

      // Resize autocompleter
      this.editor.completer.popup.container.style.width='35vw'

      // Resize after Renderer
      this.editor.renderer.on('afterRender', () => { this.editor.resize() });
    },
    highlightQueries() {
      var Range = ace.require("ace/range").Range
      var cursorPosition = this.editor.getCursorPosition()
      var cursorPositionIndex = this.editor.session.doc.positionToIndex(cursorPosition)
      var editorText = this.editor.getValue()

      // Get query positions from string
      var queries = this.analyzeQueries(editorText)

      // Get Cursor Position Index
      if (queries.length > 0) {
        cursorPositionIndex = (cursorPositionIndex > queries[queries.length-1]['end']) ? queries[queries.length-1]['end'] : cursorPositionIndex 
      }

      // Get Current Query
      var currentQuery = { query: '', start: null, end: null}
      for (let i = 0; i < queries.length; ++i) {
        if (
          (i == 0 && cursorPositionIndex < queries[0]['begin']) ||
          (cursorPositionIndex >= queries[i]['begin'] && cursorPositionIndex <= queries[i]['end'])
         ) {
          currentQuery = { query: editorText.substring(queries[i]['begin'], queries[i]['end']), start: queries[i]['begin'], end: queries[i]['end']}
          break
        }
        else if (cursorPositionIndex < queries[i]['begin']) {
          currentQuery = { query: editorText.substring(queries[i-1]['begin'], queries[i-1]['end']), start: queries[i-1]['begin'], end: queries[i-1]['end']}
          break
        }
      }
      // Get Current Query Range in Ace Editor
      var queryRange = { start: this.editor.session.doc.indexToPosition(currentQuery.start), end: this.editor.session.doc.indexToPosition(currentQuery.end)}

      // Store Current Query (+ range)
      this.clientQuery = { query: currentQuery.query, range: queryRange }

      // Remove Previous Markers
      while (this.editorMarkers.length > 0) {
        this.editor.session.removeMarker(this.editorMarkers.pop())
      }

      // Highlight Current Query
      if (currentQuery.query.trim().length > 0 && queryRange != null) {
        var marker = this.editor.session.addMarker(new Range(queryRange['start'].row, queryRange['start'].column, queryRange['end'].row, queryRange['end'].column), 'ace_active-line', true)
        this.editorMarkers.push(marker)
      }
    },
    analyzeQueries(text) {
      // Get all Query Positions
      var queries = []
      var chars = []
      var start = 0
      var delimiter = ';'
      var first = true
      for (var i = 0; i < text.length; ++i) {
        if (first && text.substring(i, i+10).toLowerCase() == 'delimiter ') {
          let found = false
          for (let j = i+10; j < text.length; ++j) {
            if ([' ','\n','\t'].includes(text[j])) {
              if (found) {  
                delimiter = text.substring(i+10, j).trim().replaceAll('\n','').replaceAll('\t','')
                i = j + 1
                start = j + 1
                break
              }
            }
            else found = true
          }
        }
        if (first) {
          if ([' ','\n','\t',';'].includes(text[i])) { start = i + 1; continue; }
          else first = false          
        }
        if (text.substring(i - delimiter.length+1, i+1) == delimiter && chars.length == 0) {
          if (!text.substring(start, i).toLowerCase().startsWith('delimiter')) {
            queries.push({"begin": start, "end": i-delimiter.length+1})
          }
          start = i + 1
          first = true
        }
        else if (["'",'"','`'].includes(text[i]) && (i == 0 || (text[i-1] != '\\' || text[i-2] == '\\'))) {
          if (chars.length == 0) chars.push(text[i])
          else if (chars[chars.length-1] == text[i]) chars.pop()
        }
        else if (chars.length == 0 && text[i] == "#") chars.push("#")
        else if (text[i] == "\n" && chars[chars.length-1] == '#') chars.pop()
        else if (text[i] == '*' && i != 0 && text[i-1] == '/') chars.push("/*")
        else if (text[i] == '/' && i != 0 && text[i-1] == '*' && chars[chars.length-1] == '/*') chars.pop()
      }
      if (i > start && !text.substring(start, i).trim().toLowerCase().startsWith('delimiter')) {
        queries.push({"begin": start, "end": i})
      }
      return queries
    },
    initExecution(payload) {
      const queries = payload.queries.map(x => x.trim().endsWith(';') ? x : x + ';').join('\n')
      this.clientHeaders = []
      this.clientItems = []
      this.bottomBar.client = { text: queries, status: 'executing', info: '' }   
      this.editor.completer.detach()
    },
    runQuery() {
      this.clientExecuting = 'query'
      const payload = {
        connection: this.id + '-main',
        server: this.server.id,
        database: this.database,
        queries: this.parseQueries()
      }
      if (payload.queries.length > 0) {
        this.initExecution(payload)
        this.executeQuery(payload)
      }
      else this.clientExecuting = null
    },
    explainQuery() {
      this.clientExecuting = 'explain'
      const payload = {
        connection: this.id + '-main',
        server: this.server.id,
        database: this.database,
        queries: this.parseQueries().reduce((acc, val) => { acc.push('EXPLAIN ' + val); return acc }, [])
      }
      if (payload.queries.length > 0) {
        this.initExecution(payload)
        this.executeQuery(payload)
      }
      else this.clientExecuting = null
    },
    beautifyQuery() {
      let query = ''
      let range = null
      const selectedText = this.editor.getSelectedText()
      // Get editor query (+ range)
      if (selectedText.length == 0) {
        query = sqlFormatter.format(this.clientQuery['query'], { reservedWordCase: 'upper', linesBetweenQueries: 2 })
        range = this.clientQuery['range']
      }
      else {
        query = sqlFormatter.format(selectedText, { reservedWordCase: 'upper', linesBetweenQueries: 2 })
        range = this.editor.selection.getRange()
      }
      // Replace selected queries with beautified format
      this.editor.session.replace(range, query)
      // Focus Editor
      let cursor = this.editor.getCursorPosition()
      this.editor.focus()
      this.editor.moveCursorTo(cursor.row, cursor.column)
    },
    minifyQuery() {
      const minify = require('pg-minify')
      let query = ''
      let range = null
      const selectedText = this.editor.getSelectedText()
      // Get editor query (+ range)
      if (selectedText.length == 0) {
        query = minify(this.clientQuery['query'])
        range = this.clientQuery['range']
      }
      else {
        query = minify(selectedText)
        range = this.editor.selection.getRange()
      }
      // Replace selected queries with beautified format
      this.editor.session.replace(range, query)
      // Focus Editor
      let cursor = this.editor.getCursorPosition()
      this.editor.focus()
      this.editor.moveCursorTo(cursor.row, cursor.column)
    },
    selectFavourite(query) {
      let cursor = this.editor.getCursorPosition()
      this.editor.session.insert(cursor, query)
      this.editor.focus()
    },
    stopQuery() {
      this.clientQueryStopped = true
      this.clientExecuting = 'stop'
      const payload = { connection: this.id + '-main' }
      const index = this.index
      axios.get('/client/stop', { params: payload })
      .finally(() => {
        let current = this.connections.find(c => c['index'] == index)
        if (current !== undefined) current.clientExecuting = null
      })
    },
    executeQuery(payload) {
      // Clean vars
      this.clientQueryStopped = false
      this.currentCellEditNode = {}
      this.currentCellEditValues = {}
      // Check database
      let database = payload.queries.find(x => x.replace(/^\s+|\s+$/g, '').substring(0,4).toUpperCase() == 'USE ')
      if (database !== undefined) {
        const parsedDatabase = database.replace(/^\s+|\s+$/g, '')
        database = database.endsWith(';') ? parsedDatabase.substring(4, parsedDatabase.length-1) : parsedDatabase.substring(4, parsedDatabase.length)
        EventBus.$emit('change-database', database)
      }
      // Show loading
      const gridApi = this.gridApi.client
      setTimeout(() => { gridApi.showLoadingOverlay() }, 0)
      // Execute queries
      const server = this.server
      const index = this.index
      axios.post('/client/execute', payload)
        .then((response) => {
          // Parse execution result
          let data = JSON.parse(response.data.data)
          // Add execution to history
          const history = { section: 'client', server: server, queries: data }
          this.$store.dispatch('client/addHistory', history)
          let current = this.connections.find(c => c['index'] == index)
          if (current === undefined) return
          this.parseExecution(payload, data, current, gridApi).finally(() => {
            this.parseClientBottomBar(data, current)
            // Focus Editor
            let cursor = this.editor.getCursorPosition()
            this.editor.focus()
            this.editor.moveCursorTo(cursor.row, cursor.column)
            current.clientExecuting = null
          })
        })
        .catch((error) => {
          let current = this.connections.find(c => c['index'] == index)
          if (current === undefined) return
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            // Get Response Data
            let data = JSON.parse(error.response.data.data)
            this.parseClientBottomBar(data, current)
            // Close Editor Completer
            this.editor.blur()
            // Show confirmation dialog
            var dialogOptions = {
              'mode': 'error',
              'icon': 'fas fa-exclamation-triangle',
              'title': 'ERROR',
              'text': data[data.length-1]['error'],
              'button1': '',
              'button2': ''
            }
            if (this.index == index) this.showDialog(dialogOptions)
            current.clientExecuting = null
            gridApi.showNoRowsOverlay()
            // Add execution to history
            const history = { section: 'client', server: server, queries: data } 
            this.$store.dispatch('client/addHistory', history)
          }
        })
    },
    parseQueries() {
      // Get Query/ies (selected or highlighted)
      const selectedText = this.editor.getSelectedText()
      var queries = []
      if (selectedText.length == 0) queries = [this.clientQuery['query']]
      else queries = this.analyzeQueries(selectedText).map(x => selectedText.substring(x.begin, x.end))
      return queries
    },
    async parseExecution(payload, data, current, gridApi) {
      // Determine if result can be edited and store current table
      const beautified = sqlFormatter.format(payload.queries.slice(-1)[0], { reservedWordCase: 'upper', linesBetweenQueries: 2 })
      let editable = true
      let found = false
      for (let line of beautified.split('\n')) {
        if (line.startsWith('FROM')) {
          // Extract DB & Table
          let raw = line.slice(5).replace(',','').replace(';','').split('`')
          if (raw[0].slice(-1) == '.') raw[0] = raw[0].slice(0, -1)
          let transform = raw.reduce((acc, val) => {
            if (!(['','.'].includes(val))) acc.push(val)
            return acc
          },[])
          if (raw.count == 1 && transform.length == 1) raw = transform[0].split('.')
          else raw = transform
          if (raw.length == 1) this.currentQueryMetadata = { database: this.database, table: raw[0].trim()}
          else this.currentQueryMetadata = { database: raw[0].trim(), table: raw[1].trim()}
          found = true
        }
        else if (found) {
          if (line.startsWith('  ')) editable = false
          break
        }
      }
      // Build Data Table
      var headers = []
      var items = data[data.length - 1]['data']
      // Build Headers
      if (data.length > 0 && data[data.length - 1]['data'].length > 0) {
        var keys = Object.keys(data[data.length - 1]['data'][0])
        for (let i = 0; i < keys.length; ++i) {
          let field = keys[i].trim()
          headers.push({ headerName: keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: editable,
            valueGetter: function(params) {
              return (params.data[field] == null) ? 'NULL' : params.data[field]
            },
            cellClassRules: {
              'ag-cell-null': params => {
                return params.data[field] == null
              },
              'ag-cell-normal': function(params) {
                return params.data[field] != null
              }
            }
          })
        }
      }
      // Load Table Header
      gridApi.setColumnDefs([])
      current.clientHeaders = headers
      // Load Table Items
      let itemsToLoad = []
      await new Promise((resolve) => {
        const n = items.length
        const chunk = 1000
        if (n == 0) resolve()
        for (let i = 0; i < n; i+=chunk) {
          if (current.clientQueryStopped) { resolve(); break }
          setTimeout(() => {
            if (!current.clientQueryStopped) {
              let sliced = items.slice(i, i+chunk)
              gridApi.applyTransaction({ add: sliced })
              itemsToLoad = itemsToLoad.concat(sliced)
              if (i+chunk >= n) resolve()
            }
            else resolve()
          }, 0)
        }
      })
      current.clientItems = itemsToLoad
    },
    onRowDataChanged() {
      if (this.columnApi.client != null) this.resizeTable()
    },
    resizeTable() {
      let allColumnIds = this.columnApi.client.getAllColumns().map(v => v.colId)
      this.columnApi.client.autoSizeColumns(allColumnIds)
    },
    parseClientBottomBar(data, current) {
      var elapsed = null
      if (data[data.length-1]['time'] !== undefined) {
        elapsed = 0
        for (let i = 0; i < data.length; ++i) {
          elapsed += parseFloat(data[i]['time'])
        }
        elapsed /= data.length
      }
      current.bottomBar.client['status'] = this.clientQueryStopped ? 'stopped' : data[data.length-1]['error'] === undefined ? 'success' : 'failure'
      current.bottomBar.client['text'] = data[data.length-1]['query'].trim().endsWith(';') ? data[data.length-1]['query'].trim() : data[data.length-1]['query'].trim() + ';'
      current.bottomBar.client['info'] = data[data.length-1]['rowCount'] !== undefined ? data[data.length-1]['rowCount'] + ' records | ' : ''
      current.bottomBar.client['info'] += data.length + ' queries'
      if (elapsed != null) current.bottomBar.client['info'] += ' | ' + elapsed.toFixed(3).toString() + 's elapsed'
    },
    showDialog(options) {
      this.dialogMode = options.mode
      this.dialogIcon = options.icon
      this.dialogTitle = options.title
      this.dialogText = options.text
      this.dialogSubmitText = options.button1
      this.dialogCancelText = options.button2
      this.dialog = true
    },
    dialogSubmit() {
      if (this.dialogMode == 'error') { this.dialog = false; this.editor.focus() } 
      else if (this.dialogMode == 'export') this.exportRowsSubmit()
      else if (this.dialogMode == 'cellEditingError') this.cellEditingEdit()
      else if (this.dialogMode == 'info') { this.dialog = false; this.$nextTick(() => this.editDialogEditor.focus()) }
    },
    dialogCancel() {
      if (this.dialogMode == 'cellEditingError') this.cellEditingDiscard()
      this.dialog = false
    },
    exportRows() {
      // Show confirmation dialog
      this.dialogSelect = 'SQL'
      var dialogOptions = {
        'mode': 'export',
        'icon': 'fas fa-arrow-down',
        'title': 'EXPORT ROWs',
        'text': '',
        'button1': 'Export',
        'button2': 'Cancel'
      }
      this.showDialog(dialogOptions)
    },
    exportRowsSubmit() {
      this.loading = true
      if (this.dialogSelect == 'Meteor') {
        let exportData = 'var DATA = ' + JSON.stringify(this.clientItems) + ';\n' + 'var COLUMNS = ' + JSON.stringify(this.clientHeaders.map(x => x.headerName.trim())) + ';'
        this.download('export.js', exportData)
      }
      else if (this.dialogSelect == 'JSON') {
        let exportData = JSON.stringify(this.clientItems)
        this.download('export.json', exportData)
      }
      else if (this.dialogSelect == 'CSV') {
        let replacer = (key, value) => value === null ? undefined : value
        let header = Object.keys(this.clientItems[0])
        let exportData = this.clientItems.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
        exportData.unshift(header.join(','))
        exportData = exportData.join('\r\n')
        this.download('export.csv', exportData)
      }
      else if (this.dialogSelect == 'SQL') {
        var SqlString = require('sqlstring');
        let rawQuery = 'INSERT INTO `<table>` (' + this.clientHeaders.map(x => '`' + x.headerName.trim() + '`').join() + ')\nVALUES\n'
        let values = ''
        let args = []
        for (let row of this.clientItems) {
          let rowVal = Object.values(row)
          args = [...args, ...rowVal];
          values += '(' + '?,'.repeat(rowVal.length).slice(0, -1) + '),\n'
        }
        rawQuery += values.slice(0,-2) + ';'
        let exportData = SqlString.format(rawQuery, args)
        this.download('export.sql', exportData)
      }
      this.loading = false
    },
    compressColumns() {
      this.resizeTable()
    },
    expandColumns() {
      this.gridApi.client.sizeColumnsToFit()
    },
    download(filename, text) {
      var element = document.createElement('a')
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text))
      element.setAttribute('download', filename)
      element.style.display = 'none'
      document.body.appendChild(element)
      element.click()
      document.body.removeChild(element)
    },
  },
}
</script>