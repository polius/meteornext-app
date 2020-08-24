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
          <ag-grid-vue ref="agGridClient" suppressColumnVirtualisation @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :stopEditingWhenGridLosesFocus="true" :columnDefs="clientHeaders" :rowData="clientItems"></ag-grid-vue>
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
            <v-icon v-if="bottomBarClient['status']=='success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:5px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBarClient['status']=='failure'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:1px; padding-right:5px;">fas fa-times-circle</v-icon>
            <span :title="bottomBarClient['text']">{{ bottomBarClient['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBarClient['info'] }}</div>
        </v-col>
      </v-row>
    </div>
  </div>
</template>

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
    }
  },
  components: { Splitpanes, Pane, AgGridVue },
  mounted () {
    EventBus.$on('RUN_QUERY', this.runQuery);
  },
  computed: {
    ...mapFields([
        'clientHeaders',
        'clientItems',
        'bottomBarClient',
        'gridApi',
        'columnApi',
        'server',
        'editorQuery',
        'editor',
        'editorMarkers',
        'editorTools',
        'loadingQuery',
        'database',
    ], { path: 'client/connection' }),
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
          if (Object.keys(this.server).length > 0 && this.editorQuery.length > 0) this.runQuery()
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
      var queries = []
      var start = 0;
      var chars = []
      for (var i = 0; i < editorText.length; ++i) {
        if (editorText[i] == ';' && chars.length == 0) {
          queries.push({"begin": start, "end": i})
          start = i+1
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
      if (start < i && editorText.substring(start, i).trim().length > 0) queries.push({"begin": start, "end": i})

      // Get Cursor Position Index
      if (queries.length > 0) {
        cursorPositionIndex = (cursorPositionIndex > queries[queries.length-1]['end']) ? queries[queries.length-1]['end'] : cursorPositionIndex 
      }

      // Get Current Query
      var query = ''
      for (let i = 0; i < queries.length; ++i) {
        if (cursorPositionIndex >= queries[i]['begin'] && cursorPositionIndex <= queries[i]['end']) {
          query = editorText.substring(queries[i]['begin'], queries[i]['end'])
          break
        }
      }
      this.editorQuery = query

      // Get Current Query Position
      var queryPosition = 0
      for (let i = 0; i < queries.length; ++i) {
        var re = new RegExp('\\b' + query.trim().replace(/[.*+\-?^${}()|[\]\\]/g, '\\$&') + '\\b');
        if (
          re.test(editorText.substring(queries[i]['begin'], queries[i]['end']).trim()) ||
          query.trim().localeCompare(editorText.substring(queries[i]['begin'], queries[i]['end']).trim()) == 0
        ) {
          if (cursorPositionIndex > queries[i]['end']) queryPosition += 1
          else break
        }
      }

      // Find Current Query in Ace Editor
      this.editor.$search.setOptions({
        needle: query.trim(),
        caseSensitive: true,
        wholeWord: true,
        regExp: false,
      }); 
      var queryRange = this.editor.$search.findAll(this.editor.session)

      // Remove Previous Markers
      while (this.editorMarkers.length > 0) {
        this.editor.session.removeMarker(this.editorMarkers.pop())
      }

      // Highlight Current Query
      if (query.trim().length > 0 && queryRange.length > 0) {
        var marker = this.editor.session.addMarker(new Range(queryRange[queryPosition]['start'].row, queryRange[queryPosition]['start'].column, queryRange[queryPosition]['end'].row, queryRange[queryPosition]['end'].column), 'ace_active-line', true)
        this.editorMarkers.push(marker)
      }
    },
    runQuery() {
      this.clientHeaders = []
      this.clientItems = []
      this.bottomBarClient = { text: '', status: '', info: '' }
      this.loadingQuery = true     
      this.editor.completer.detach()
      this.gridApi.client.showLoadingOverlay()
      const payload = {
        server: this.server.id,
        database: this.database,
        queries: this.parseQueries()
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          this.parseExecution(JSON.parse(response.data.data))
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
              'mode': 'queryError',
              'title': 'Error Message',
              'text': data[data.length-1]['error'],
              'button1': 'Close',
              'button2': ''
            }
            this.showDialog(dialogOptions['mode'], dialogOptions['title'], dialogOptions['text'], dialogOptions['button1'], dialogOptions['button2'])
          }
        })
        .finally(() => {
          this.loadingQuery = false
        })
    },
    parseQueries() {
      // Get Query/ies (selected or highlighted)
      const selectedText = this.editor.getSelectedText()
      var queries = []
      if (selectedText.length == 0) queries = [this.editorQuery]
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
      this.bottomBarClient['status'] = data[data.length-1]['error'] === undefined ? 'success' : 'failure'
      this.bottomBarClient['text'] = data[data.length-1]['query'].endsWith(';') ? data[data.length-1]['query'] : data[data.length-1]['query'] + ';'
      this.bottomBarClient['info'] = (data[data.length-1]['data'] !== undefined && data[data.length-1]['query'].toLowerCase().startsWith('select')) ? data[data.length-1]['data'].length + ' records | ' : ''
      this.bottomBarClient['info'] += data.length + ' queries'
      if (elapsed != null) this.bottomBarClient['info'] += ' | ' + elapsed.toString() + 's elapsed'
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
      this.showDialog(dialogOptions['mode'], dialogOptions['title'], dialogOptions['text'], dialogOptions['button1'], dialogOptions['button2']) 
    },
  },
}
</script>