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
          <ag-grid-vue ref="agGridClient" suppressContextMenu preventDefaultOnContextMenu suppressColumnVirtualisation @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" @cell-context-menu="onContextMenu" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :stopEditingWhenGridLosesFocus="true" :columnDefs="clientHeaders" :rowData="clientItems"></ag-grid-vue>
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
        <v-col v-if="clientItems.length > 0" cols="auto">
          <v-btn @click="exportRows('client')" text small title="Export rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-arrow-down</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBar.client['status']=='success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:5px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBar.client['status']=='failure'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:1px; padding-right:5px;">fas fa-times-circle</v-icon>
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
    <v-dialog v-model="dialog" persistent max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">{{ dialogTitle }}</div>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:20px; margin-bottom:15px;">
                  <div v-if="dialogText.length>0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogText }}</div>
                  <v-select v-if="dialogMode=='export'" outlined v-model="dialogSelect" :items="['Meteor','JSON','CSV','SQL']" label="Format" hide-details></v-select>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogSubmitText.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="primary">{{ dialogSubmitText }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogCancelText.length > 0" style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialogCancel" outlined color="#e74d3c">{{ dialogCancelText }}</v-btn>
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

import * as ace from 'ace-builds';
import 'ace-builds/webpack-resolver';
import 'ace-builds/src-noconflict/ext-language_tools';

import {AgGridVue} from "ag-grid-vue";
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      dialogMode: '',
      dialogTitle: '',
      dialogText: '',
      dialogSubmitText: '',
      dialogCancelText: '',
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
    EventBus.$on('RUN_QUERY', this.runQuery);
    EventBus.$on('EXPLAIN_QUERY', this.explainQuery);
  },
  computed: {
    ...mapFields([
      'headerTabSelected',
      'clientHeaders',
      'clientItems',
      'bottomBar',
      'server',
      'clientQuery',
      'clientQueryExecuting',
      'database',
      'sidebarSelected',
    ], { path: 'client/connection' }),
    ...mapFields([
      'editor',
      'editorMarkers',
      'editorTools',
      'gridApi',
      'columnApi',
    ], { path: 'client/components' }),
  },
  watch: {
    headerTabSelected(val) {
      if (val == 'client') {
        this.$nextTick(() => {
          if (this.gridApi.client != null) this.resizeTable()
        })
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
      }
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        navigator.clipboard.writeText(e.value)

        // Highlight cells
        e.event.originalTarget.classList.add('ag-cell-highlight');
        e.event.originalTarget.classList.remove('ag-cell-highlight-animation')

        // Add animation
        window.setTimeout(function () {
          e.event.originalTarget.classList.remove('ag-cell-highlight')
          e.event.originalTarget.classList.add('ag-cell-highlight-animation')
          e.event.originalTarget.style.transition = "background-color " + 200 + "ms"

          // Remove animation
          window.setTimeout(function () {
              e.event.originalTarget.classList.remove('ag-cell-highlight-animation')
              e.event.originalTarget.style.transition = null;
          }, 200);
        }, 200);
      }
    },
    onContextMenu(e) {
      e.node.setSelected(true)
      this.contextMenuModel = null
      this.contextMenuX = e.event.clientX
      this.contextMenuY = e.event.clientY
      this.contextMenu = true
    },
    contextMenuClicked(item) {
      if (item.startsWith('Copy')) {
        let selected = this.gridApi.client.getSelectedRows()
        if (item == 'Copy SQL') {
          console.log(selected)
        }
        else if (item == 'Copy CSV') {
          console.log(selected)
        }
        else if (item == 'Copy JSON') {
          console.log(selected)
        }
      }
      else if (item == 'Select All') this.gridApi.client.selectAll()
      else if (item == 'Deselect All') this.gridApi.client.deselectAll()
    },
    initAceClient() {
      // Editor Settings
      this.editor = ace.edit("editor", {
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
      this.editor.session.setOptions({ tabSize: 4, useSoftTabs: false })
      this.editorTools = ace.require("ace/ext/language_tools")

      // Highlight Queries
      this.editor.on("changeSelection", this.highlightQueries)

      // Add custom keybinds
      this.editor.commands.removeCommand('transposeletters')
      this.editor.container.addEventListener("keydown", (e) => {
        // if (e.key.toLowerCase() == "w" && (navigator.platform.match("Mac") ? e.metaKey : e.ctrlKey))
        // - New Connection -
        if (e.key.toLowerCase() == "t" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          this.newConnection()
        }
        // - Remove Connection -
        else if (e.key.toLowerCase() == "w" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          this.removeConnection(this.currentConn)
        }
        // - Run Query/ies -
        else if (e.key.toLowerCase() == "r" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          if (Object.keys(this.server).length > 0 && this.clientQuery.length > 0) this.runQuery()
        }
        // - Explain Query/ies -
        else if (e.key.toLowerCase() == "e" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault()
          if (Object.keys(this.server).length > 0 && this.clientQuery.length > 0) this.explainQuery()
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
      }, false);

      // Convert Completer Keywords to Uppercase
      const defaultUpperCase = {
        getCompletions(editor, session, pos, prefix, callback) {
          if (session.$mode.completer) {
            return session.$mode.completer.getCompletions(editor, session, pos, prefix, callback);
          }
          const state = editor.session.getState(pos.row);
          let keywordCompletions;
          // if (prefix === prefix.toUpperCase()) {
            keywordCompletions = session.$mode.getCompletions(state, session, pos, prefix);
            keywordCompletions = keywordCompletions.map((obj) => {
              const copy = obj;
              copy.value = obj.value.toUpperCase();
              return copy;
            });
          // } else {
          //   keywordCompletions = session.$mode.getCompletions(state, session, pos, prefix);
          // }
          return callback(null, keywordCompletions);
        },
      };
      this.editor.completers = [defaultUpperCase]

      // Resize after Renderer
      this.editor.renderer.on('afterRender', () => { this.editor.resize() });

      // Focus Editor
      this.editor.focus()
    },
    highlightQueries() {
      var Range = ace.require("ace/range").Range
      var cursorPosition = this.editor.getCursorPosition()
      var cursorPositionIndex = this.editor.session.doc.positionToIndex(cursorPosition)
      var editorText = this.editor.getValue()

      // Get all Query Positions
      var rawQueries = []
      var start = 0;
      var chars = []
      for (var i = 0; i < editorText.length; ++i) {
        if (editorText[i] == ';' && chars.length == 0) {
          rawQueries.push({"begin": start, "end": i+1})
          start = i+2
        }
        else if (editorText[i] == "\"") {
          if (chars[chars.length-1] == '"') chars.pop()
          else chars.push("\"")
        }
        else if (editorText[i] == "'") {
          if (chars[chars.length-1] == "'") chars.pop()
          else chars.push("'")
        }
      }
      if (start < i && editorText.substring(start, i).trim().length > 0) rawQueries.push({"begin": start, "end": i})

      // Parse Complex Queries (Triggers, Functions, Procedures, Events)
      var queries = []
      var detected = false
      for (let i = 0; i < rawQueries.length; ++i) {
        let query = editorText.substring(rawQueries[i]['begin'], rawQueries[i]['end'])
        let queryLower = query.toLowerCase().trim()
        if (detected) {
          if (queryLower.startsWith('end') && queryLower.includes(';')) detected = false
          queries[queries.length-1]['end'] = rawQueries[i]['end']
        }
        else {
          if (queryLower.startsWith('create ') && (queryLower.includes(' trigger ') || queryLower.includes(' function ') || queryLower.includes(' procedure ') || queryLower.includes(' event '))) detected = true
          queries.push({"begin": rawQueries[i]['begin'], "end": rawQueries[i]['end']})
        }
      }

      // Get Cursor Position Index
      if (queries.length > 0) {
        cursorPositionIndex = (cursorPositionIndex > queries[queries.length-1]['end']) ? queries[queries.length-1]['end'] : cursorPositionIndex 
      }

      // Get Current Query
      var query = ''
      var queryStart = null
      for (let i = 0; i < queries.length; ++i) {
        if (cursorPositionIndex >= queries[i]['begin'] && cursorPositionIndex <= queries[i]['end']) {
          query = editorText.substring(queries[i]['begin'], queries[i]['end'])
          queryStart = queries[i]['begin']
          break
        }
      }
      this.clientQuery = query

      // Find Current Query in Ace Editor
      let queryPosition = this.editor.session.doc.indexToPosition(queryStart)
      this.editor.$search.setOptions({
        needle: query.trim(),
        caseSensitive: true,
        wholeWord: true,
        regExp: false,
        start: queryPosition
      }); 
      var queryRange = this.editor.$search.find(this.editor.session)

      // Remove Previous Markers
      while (this.editorMarkers.length > 0) {
        this.editor.session.removeMarker(this.editorMarkers.pop())
      }

      // Highlight Current Query
      if (query.trim().length > 0 && queryRange != null) {
        var marker = this.editor.session.addMarker(new Range(queryRange['start'].row, queryRange['start'].column, queryRange['end'].row, queryRange['end'].column), 'ace_active-line', true)
        this.editorMarkers.push(marker)
      }
    },
    initExecution() {
      this.clientHeaders = []
      this.clientItems = []
      this.bottomBar.client = { text: '', status: '', info: '' }
      this.clientQueryExecuting = true     
      this.editor.completer.detach()
      this.gridApi.client.showLoadingOverlay()
    },
    runQuery() {
      this.initExecution()
      const payload = {
        server: this.server.id,
        database: this.database,
        queries: this.parseQueries()
      }
      this.executeQuery(payload)
    },
    explainQuery() {
      this.initExecution()
      const payload = {
        server: this.server.id,
        database: this.database,
        queries: this.parseQueries().reduce((acc, val) => { acc.push('EXPLAIN ' + val); return acc }, [])
      }
      this.executeQuery(payload)
    },
    executeQuery(payload) {
      axios.post('/client/execute', payload)
        .then((response) => {
          this.parseExecution(JSON.parse(response.data.data))
          // Focus Editor
          let cur = this.editor.getCursorPosition()
          this.editor.focus()
          this.editor.moveCursorTo(cur.row, cur.column);
        })
        .catch((error) => {
          console.log(error)
          this.gridApi.client.hideOverlay()
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            // Get Response Data
            let data = JSON.parse(error.response.data.data)
            this.parseClientBottomBar(data)
            // Close Editor Completer
            this.editor.blur()
            // Show confirmation dialog
            var dialogOptions = {
              'mode': 'error',
              'title': 'Error Message',
              'text': data[data.length-1]['error'],
              'button1': 'Close',
              'button2': ''
            }
            this.showDialog(dialogOptions)
          }
        })
        .finally(() => {
          this.clientQueryExecuting = false
        })
    },
    parseQueries() {
      // Get Query/ies (selected or highlighted)
      const selectedText = this.editor.getSelectedText()
      var queries = []
      if (selectedText.length == 0) queries = [this.clientQuery]
      else {
        // Build multi-queries
        let start = 0;
        let chars = []
        for (var i = 0; i < selectedText.length; ++i) {
          if (selectedText[i] == ';' && chars.length == 0) {
            queries.push(selectedText.substring(start, i+1).trim())
            start = i+1
          }
          else if (selectedText[i] == "\"") {
            if (chars[chars.length-1] == '"') chars.pop()
            else chars.push("\"")
          }
          else if (selectedText[i] == "'") {
            if (chars[chars.length-1] == "'") chars.pop()
            else chars.push("'")
          }
        }
        if (start < i) queries.push(selectedText.substring(start, i).trim())
      }
      // Return parsed queries
      return queries
    },
    parseExecution(data) {
      // Build Data Table
      var headers = []
      var items = data[data.length - 1]['data']
      // Build Headers
      if (data.length > 0 && data[0]['data'].length > 0) {
        var keys = Object.keys(data[data.length - 1]['data'][0])
        for (let i = 0; i < keys.length; ++i) {
          let field = keys[i].trim()
          headers.push({ headerName: keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true })
        }
      }
      this.clientHeaders = headers
      this.clientItems = items

      // Resize Table
      this.gridApi.client.setColumnDefs(headers)
      this.resizeTable()

      // Build BottomBar
      this.parseClientBottomBar(data)
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.client.getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.client.autoSizeColumns(allColumnIds);
    },
    parseClientBottomBar(data) {
      var elapsed = null
      if (data[data.length-1]['time'] !== undefined) {
        elapsed = 0
        for (let i = 0; i < data.length; ++i) {
          elapsed += parseFloat(data[i]['time'])
        }
        elapsed /= data.length
      }
      this.bottomBar.client['status'] = data[data.length-1]['error'] === undefined ? 'success' : 'failure'
      this.bottomBar.client['text'] = data[data.length-1]['query'].endsWith(';') ? data[data.length-1]['query'] : data[data.length-1]['query'] + ';'
      this.bottomBar.client['info'] = (data[data.length-1]['data'] !== undefined && data[data.length-1]['query'].toLowerCase().startsWith('select')) ? data[data.length-1]['data'].length + ' records | ' : ''
      this.bottomBar.client['info'] += data.length + ' queries'
      if (elapsed != null) this.bottomBar.client['info'] += ' | ' + elapsed.toString() + 's elapsed'
    },
    showDialog(options) {
      this.dialogMode = options.mode
      this.dialogTitle = options.title
      this.dialogText = options.text
      this.dialogSubmitText = options.button1
      this.dialogCancelText = options.button2
      this.dialog = true
    },
    dialogSubmit() {
      if (this.dialogMode == 'error') { 
        this.dialog = false
        this.editor.focus()
      } 
      else if (this.dialogMode == 'export') this.exportRowsSubmit()
    },
    dialogCancel() {
      this.dialog = false
    },
    exportRows() {
      // Show confirmation dialog
      this.dialogSelect = 'Meteor'
      var dialogOptions = {
        'mode': 'export',
        'title': 'Export Rows',
        'text': '',
        'button1': 'Export',
        'button2': 'Cancel'
      }
      this.showDialog(dialogOptions)
    },
    exportRowsSubmit() {
      var columns = []
      var rows = []

      // Build Columns
      let displayedColumns = this.columnApi.content.getAllDisplayedColumns()
      for (var i = 0; i < displayedColumns.length; ++i) columns.push(displayedColumns[i]['colId']);

      // Build Rows
      if (['Meteor','JSON','CSV'].includes(this.dialogSelect)) {
        this.gridApi.content.forEachNode(function(rowNode) {
          rows.push(rowNode.data)
        })
      }

      if (this.dialogSelect == 'Meteor') {
        let exportData = 'var DATA = ' + JSON.stringify(rows) + ';\n' + 'var COLUMNS = ' + JSON.stringify(columns) + ';'
        this.download('export.js', exportData)
      }
      else if (this.dialogSelect == 'JSON') {
        let exportData = JSON.stringify(rows)
        this.download('export.json', exportData)
      }
      else if (this.dialogSelect == 'CSV') {
        let replacer = (key, value) => value === null ? '' : value // specify how you want to handle null values here
        let header = Object.keys(rows[0])
        let exportData = rows.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
        exportData.unshift(header.join(','))
        exportData = exportData.join('\r\n')
        this.download('export.csv', exportData)
      }
      else if (this.dialogSelect == 'SQL') {
        let exportData = ''
        this.gridApi.content.forEachNode(rowNode => {
          let data = []
          for (let i = 0; i < columns.length; ++i) {
            if (rowNode.data[columns[i]] == null) data.push('NULL')
            else data.push(JSON.stringify(rowNode.data[columns[i]]))
          }
          exportData += "INSERT INTO " + this.sidebarSelected['name'] + ' (' + columns.join() + ") VALUES (" + data.join() + "),\n"
        })
        exportData = exportData.slice(0, -2) + ';'
        this.download('export.sql', exportData)
      }
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