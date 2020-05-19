<template>
  <v-content>
    <div>
      <v-tabs show-arrows background-color="#9b59b6" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
        <v-tabs-slider></v-tabs-slider>
          <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-bolt</v-icon>CLIENT</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab :disabled="treeviewMode != 'tables' || treeview.length == 0"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-dice-d6</v-icon>Structure</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab :disabled="treeviewMode != 'tables' || treeview.length == 0"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">far fa-window-maximize</v-icon>Content</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab :disabled="treeviewMode != 'tables' || treeview.length == 0"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-sitemap</v-icon>Relations</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab :disabled="treeviewMode != 'tables' || treeview.length == 0"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-fire</v-icon>Triggers</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab :disabled="treeviewMode != 'tables' || treeview.length == 0"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-th</v-icon>Table Info</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <!-- <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px; font-size:14px;">fas fa-terminal</v-icon>Query</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider> -->
          <v-spacer></v-spacer>
          <v-tab title="Users" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-user-shield</v-icon></span></v-tab>
          <v-tab title="Saved Queries" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-star</v-icon></span></v-tab>
          <v-tab title="Query History" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-history</v-icon></span></v-tab>
          <v-tab title="Settings" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-cog</v-icon></span></v-tab>
        </v-tabs>
    </div>
    <v-container fluid>
      <v-content style="padding-top:0px; padding-bottom:0px;">
        <div style="margin: -12px;">
          <div ref="masterDiv" style="height: calc(100vh - 145px);">
            <Splitpanes>
              <Pane size="20" min-size="0">
                <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
                  <v-select v-model="database" @change="getTables" solo :disabled="databaseItems.length == 0" :items="databaseItems" label="Database" hide-details background-color="#303030" style="padding: 10px 10px 10px 10px;"></v-select>
                  <div class="subtitle-2" style="padding-left:10px; padding-top:10px; color:rgb(222,222,222);">{{ treeviewMode == 'servers' ? 'SERVERS' : 'TABLES & VIEWS' }}</div>
                  <v-treeview :disabled="loadingServer" @contextmenu="show" :active.sync="treeview" item-key="id" :open="treeviewOpen" :items="treeviewItems" :search="treeviewSearch" activatable open-on-click transition class="clear_shadow" style="height:calc(100% - 160px); padding-top:7px; width:100%; overflow-y:auto;">
                    <template v-slot:label="{item, open}">        
                      <v-btn text @dblclick="doubleClick(item)" @contextmenu="show" style="font-size:14px; text-transform:none; font-weight:400; width:100%; justify-content:left; padding:0px;"> 
                        <!--button icon-->
                        <v-icon v-if="!item.type" small style="padding:10px;">
                          {{ open ? 'mdi-folder-open' : 'mdi-folder' }}
                        </v-icon>
                        <v-icon v-else small :title="item.type" :color="treeviewColor[item.type]" style="padding:10px;">
                          {{ treeviewImg[item.type] }}
                        </v-icon>
                        <!--button text-->
                        {{item.name}}
                        <v-spacer></v-spacer>
                        <v-progress-circular v-if="loadingServer && item.id == treeview[0]" indeterminate size="16" width="2" color="white" style="margin-right:10px;"></v-progress-circular>
                      </v-btn>
                    </template>
                  </v-treeview>
                  <v-menu v-model="showMenu" :position-x="x" :position-y="y" absolute offset-y>
                    <v-list style="padding:0px;">
                      <v-list-item v-for="menuItem in menuItems" :key="menuItem" @click="clickAction">
                        <v-list-item-title>{{menuItem}}</v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </v-menu>
                  <v-text-field v-model="treeviewSearch" label="Search" dense solo hide-details style="float:left; width:100%; padding:10px;"></v-text-field>
                </div>
              </Pane>
              <Pane size="80" min-size="0">
                <Splitpanes horizontal @ready="initAce()" @resize="resize($event)">
                  <Pane size="50">
                    <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
                      <v-tabs v-if="connections.length > 0" show-arrows dense background-color="#303030" color="white" v-model="currentConn" slider-color="white" slot="extension" class="elevation-2" style="max-width:calc(100% - 97px); float:left;">
                        <v-tabs-slider></v-tabs-slider>
                        <v-tab v-for="(t, index) in connections" :key="index" @click="changeConnection(index)" :title="'Name: ' + t.server.name + '\nHost: ' + t.server.host" style="padding:0px 10px 0px 0px; text-transform:none;">
                          <span class="pl-2 pr-2"><v-btn title="Close Connection" small icon @click.prevent.stop="removeConnection(index)" style="margin-right:10px;"><v-icon x-small style="padding-bottom:1px;">fas fa-times</v-icon></v-btn>{{ t.server.name }}</span>
                        </v-tab>
                        <v-divider class="mx-3" inset vertical></v-divider>
                        <v-btn text title="New Connection" @click="newConnection()" style="height:100%; font-size:16px;">+</v-btn>
                      </v-tabs>
                      <v-btn :disabled="editorQuery.length == 0" v-if="connections.length > 0" @click="runQuery()" style="margin:6px;" title="Execute Query"><v-icon small style="padding-right:10px;">fas fa-bolt</v-icon>Run</v-btn>
                      <!-- <v-btn :disabled="editorQuery.length == 0" v-if="connections.length > 0" @click="runQuery()" style="margin:6px;" title="Export Results"><v-icon small style="padding-right:10px;">fas fa-file-export</v-icon>Export Results</v-btn> -->
                      <div id="editor" style="float:left"></div>
                    </div>
                  </Pane>
                  <Pane size="50" min-size="0">
                    <ag-grid-vue suppressColumnVirtualisation @grid-ready="onGridReady" @model-updated="onGridUpdated" style="width:100%; height:100%;" class="ag-theme-alpine-dark" :columnDefs="resultsHeaders" :rowData="resultsItems"></ag-grid-vue>
                  </Pane>
                </Splitpanes>
              </Pane>
            </Splitpanes>
          </div>
          <div style="width:100%; padding-top:6px; padding-left:20px; padding-right:20px; border-top:1px solid rgba(37, 37, 37, 0.5);">
            <div class="body-2" style="float:left; width:calc(100vw - 180px); text-align:center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">5 rows affected</div>
            <div class="body-2" style="float:right; text-align:right;">0.046s elapsed</div>
          </div>
          <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
            {{ snackbarText }}
            <v-btn color="white" text @click="snackbar = false">Close</v-btn>
          </v-snackbar>
        </div>
      </v-content>
    </v-container>
  </v-content>
</template>

<style>
@import "../../../node_modules/ag-grid-community/dist/styles/ag-grid.css";
@import "../../../node_modules/ag-grid-community/dist/styles/ag-theme-alpine-dark.css";

.splitpanes__pane {
  box-shadow: 0 0 3px rgba(0, 0, 0, .2) inset;
  justify-content: center;
  align-items: center;
  display: flex;
  position: relative;
}
.splitpanes--vertical > .splitpanes__splitter {
  min-width: 5px;
}
.splitpanes--horizontal > .splitpanes__splitter {
  min-height: 5px;
}
.ace_editor {
  margin: auto;
  height: 100%;
  width: 100%;
  background: #272822;
}
.ace_content {
  width: 100%;
  height: 100%;
}
.v-treeview-node__root {
  min-height:30px;
}
.v-treeview-node__toggle {
  width: 15px;
}

.splitpanes__splitter {background-color:rgba(32, 32, 32, 0.2); position: relative; }
.splitpanes__splitter:before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  transition: opacity 0.4s;
  background-color: rgba(32, 32, 32, 0.3);
  opacity: 0;
  z-index: 10;
}
.splitpanes__splitter:hover:before  {opacity:1; }
.splitpanes--vertical > .splitpanes__splitter:before { left:-3px; right:-3px; height:100%; }
.splitpanes--horizontal > .splitpanes__splitter:before { top:-5px; bottom:-3px; width:100%; }

.theme--dark.v-data-table.v-data-table--fixed-header thead th {
  background-color: #252525;
}
.v-treeview-node__level {
  width: 10px;
}
.v-label{
  font-size: 0.9rem;
}
.v-list-item__title {
  font-size: 0.9rem;
}
.v-list-item__content {
  padding:0px;
}
.v-list-item {
  min-height:40px;
}
.v-input {
  font-size: 0.9rem;
}
.v-application .elevation-2 {
  box-shadow:none!important;
}
.container {
  padding-bottom:0px;
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

export default {
  data() {
    return {
      // Tabs Header
      tabs: null,

      // Connections
      connections: [],
      currentConn: 0,
      nconn: 0,
      servers: [],

      // Loadings
      loadingServer: false,
      loadingQuery: false,

      // Database Selector
      databaseItems: [],
      database: '',

      // Servers Tree View
      treeviewOpen: [],
      treeviewImg: {
        MySQL: "fas fa-server",
        PostgreSQL: "fas fa-server",
        Table: "fas fa-th",
        View: "fas fa-th"
      },
      treeviewColor: {
        MySQL: "",
        PostgreSQL: "",
        Table: "#ec644b",
        View: "#f2d984"
      },
      treeview: [],
      treeviewItems: [],
      treeviewMode: 'servers',
      treeviewSearch: '',

      // Menu (right click)
      showMenu: false,
      x: 0,
      y: 0,
      menuItems: ["Rename", "Truncate", "Delete", "Duplicate", "Export"],

      // ACE Editor
      editor: null,
      editorTools: null,
      editorMarkers: [],
      editorQuery: '',

      // Results Table Data
      resultsHeaders: [],
      resultsItems: [],

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(5000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  components: { Splitpanes, Pane, AgGridVue },
  created() {
    this.getServers()
  },
  methods: {
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      this.gridApi.sizeColumnsToFit()
    },
    onGridUpdated() {
      if (typeof this.gridApi !== 'undefined') {
        var allColumnIds = [];
        this.columnApi.getAllColumns().forEach(function(column) {
          allColumnIds.push(column.colId);
        });
        this.columnApi.autoSizeColumns(allColumnIds);
      }
    },
    initAce() {
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

      // Highlight Queries
      this.editor.getSelection().on("changeCursor", this.highlightQueries)

      // Add custom keybinds
      // console.log(this.editor.keyBinding.$defaultHandler.commandKeyBinding)
      this.editor.commands.removeCommand('transposeletters')
      this.editor.container.addEventListener("keydown", (e) => {
        // if (e.key.toLowerCase() == "w" && (navigator.platform.match("Mac") ? e.metaKey : e.ctrlKey))
        // - New Connection -
        if (e.key.toLowerCase() == "t" && (e.ctrlKey || e.metaKey)) {
          this.newConnection()
          e.preventDefault()
        }
        // - Remove Connection -
        else if (e.key.toLowerCase() == "w" && (e.ctrlKey || e.metaKey)) {
          this.removeConnection(this.currentConn)
          e.preventDefault()
        }
        // - Run Query/ies -
        else if (e.key.toLowerCase() == "r" && (e.ctrlKey || e.metaKey)) {
          if (this.connections.length > 0 && this.editorQuery.length > 0) this.runQuery()
          e.preventDefault()
        }
        // - Increase Font Size -
        else if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
          let size = parseInt(this.editor.getFontSize(), 10) || 12
          this.editor.setFontSize(size + 1)
          e.preventDefault()
        }
        // - Decrease Font Size -
        else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
          let size = parseInt(this.editor.getFontSize(), 10) || 12
          this.editor.setFontSize(Math.max(size - 1 || 1))
          e.preventDefault()
        }
      }, false);

      // Convert Completer to Uppercase
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

      // Add custom Completer
      var myList = [
        "/dev/sda1",
        "/dev/sda2"
      ]
      var myCompleter = {
        identifierRegexps: [/[^\s]+/],
        getCompletions: function(editor, session, pos, prefix, callback) {
          callback(
            null,
            myList.filter(entry=>{
              return entry.includes(prefix)
            }).map(entry=>{
              return {
                value: entry
              };
            })
          );
        }
      }

      this.editor.completers = [
        defaultUpperCase,
        myCompleter,
      ];

      // Add Custom Completer (Databases and tables names)
      // this.editorTools = ace.require("ace/ext/language_tools")
      // this.editorTools.addCompleter(myCompleter)

      // Resize after Renderer
      this.editor.renderer.on('afterRender', this.resize);

      // Focus Editor
      this.editor.focus()
    },
    check(e) {
      console.log(e)
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
        var re = new RegExp('\\b' + query.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b',"g");
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
    doubleClick(item) {
      if (!('children' in item) && this.treeviewMode == 'servers') this.getDatabases(item)
    },
    getServers() {
      axios.get('/client/servers')
        .then((response) => {
          this.parseServers(response.data.data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    parseServers(data) {
      var servers = []
      for (let i = 0; i < data.length; ++i) {
        let found = false
        for (var j = 0; j < servers.length; ++j) {
          if (servers[j]['id'] == 'r' + data[i]['region_id']) {
            found = true
            break
          }
        }
        if (found) servers[j]['children'].push({ id: data[i]['server_id'], name: data[i]['server_name'], type: data[i]['server_engine'], host: data[i]['server_hostname'] })
        else servers.push({ id: 'r' + data[i]['region_id'], name: data[i]['region_name'], children: [{ id: data[i]['server_id'], name: data[i]['server_name'], type: data[i]['server_engine'], host: data[i]['server_hostname'] }] })
      }
      this.treeviewItems = servers.slice(0)
      this.servers = servers.slice(0)
    },
    getDatabases(server) {
      // Select Server
      this.treeview = [server.id]
      this.loadingServer = true
      this.serverSelected = server

      // Retrieve Databases
      axios.get('/client/databases', { params: { server_id: server.id } })
        .then((response) => {
          this.treeview = []
          this.treeviewItems = []
          this.treeviewMode = 'tables'
          this.databaseItems = response.data.data
          const connection = { server: server, databases: response.data.data }
          if (this.connections.length == 0) this.connections.push(connection)
          else this.connections[this.currentConn] = connection
          this.editor.focus()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loadingServer = false
        })
    },
    getTables(database) {
      // Retrieve Tables
      axios.get('/client/tables', { params: { server_id: this.serverSelected.id, database_name: database } })
        .then((response) => {
          this.parseTables(response.data.data)
          this.editor.focus()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    parseTables(data) {
      var tables = []
      for (let i = 0; i < data.length; ++i) {
        tables.push({ id: data[i]['table_name'], name: data[i]['table_name'], type: (data[i]['is_view'] == 0) ? 'Table' : 'View' })
      }
      this.treeviewItems = tables
    },
    newConnection() {
      if (this.connections.length == 0) return

      // Store connection
      this.__storeConn(this.currentConn)

      // Add new connection
      this.nconn += 1
      var newConn = {
        server: { name: 'Connection ' + this.nconn },
        databases: [],
        database: '',
        treeview: [],
        treeviewItems: this.servers.slice(0),
        treeviewMode: 'servers',
        treeviewSearch: '',
        editor: '',
        resultsHeaders: [],
        resultsItems: []
      }
      this.connections.push(newConn)
      this.currentConn = this.connections.length - 1
      this.__loadConn(this.currentConn)
    },
    removeConnection(index) {
      if (this.connections.length == 0) return
      this.connections.splice(index, 1)
      if (this.connections.length == 0) {
        this.databaseItems = []
        this.database = ''
        this.treeview = []
        this.treeviewItems = this.servers.slice(0)
        this.treeviewMode = 'servers'
        this.treeviewSearch = ''
        this.editor.setValue('')
        this.resultsHeaders = []
        this.resultsItems = []
      }
      else if (index == this.currentConn) {
        if (this.connections.length > index) this.__loadConn(index)
        else this.__loadConn(index-1)
      }
      else if (this.currentConn > index) this.currentConn = index + 1
    },
    changeConnection(index) {
      if (this.currentConn != index) {       
        // Store connection
        this.__storeConn(this.currentConn)

        // Load connection
        this.__loadConn(index)

        // Change connection
        this.currentConn = index
      }
    },
    __storeConn(index) {
      // Store Connection
      this.connections[index] = {
        server: JSON.parse(JSON.stringify(this.connections[index]['server'])),
        databases: this.databaseItems.slice(0),
        database: this.database,
        treeview: this.treeview.slice(0),
        treeviewItems: this.treeviewItems.slice(0),
        treeviewMode: this.treeviewMode,
        treeviewSearch: this.treeviewSearch,
        editor: this.editor.getValue(),
        resultsHeaders: this.resultsHeaders.slice(0),
        resultsItems: this.resultsItems.slice(0)
      }
    },
    __loadConn(index) {
      this.databaseItems = this.connections[index]['databases'].slice(0)
      this.database = this.connections[index]['database']
      this.treeview = this.connections[index]['treeview'].slice(0)
      this.treeviewItems = this.connections[index]['treeviewItems'].slice(0)
      this.treeviewMode = this.connections[index]['treeviewMode']
      this.treeviewSearch = this.connections[index]['treeviewSearch']
      this.editor.setValue(this.connections[index]['editor'])
      this.resultsHeaders = this.connections[index]['resultsHeaders'].slice(0)
      this.resultsItems = this.connections[index]['resultsItems'].slice(0)
    },
    runQuery() {
      this.resultsHeaders = []
      this.resultsItems = []
      this.loadingQuery = true
      const payload = {
        server: this.serverSelected.id,
        database: this.database,
        queries: this.__parseQueries()
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          this.parseResult(response.data.data)
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loadingQuery = false
        })
    },
    parseResult(data) {
      // Build Data Table
      console.log(data)
      var headers = []
      var items = data['query_result']
      // - Build Headers -
      var keys = Object.keys(data['query_result'][0])
      for (let i = 0; i < keys.length; ++i) {
        headers.push({ headerName: keys[i], field: keys[i].trim().toLowerCase(), sortable: true, filter: true, resizable: true, editable: true })
      }
      this.resultsHeaders = headers
      this.resultsItems = items
    },
    __parseQueries() {
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
    resize() {
      // Resize Ace Code Editor
      this.editor.resize();
    },
    clickAction(){
      alert('clicked');
    },
    show(e) {
      e.preventDefault();
      this.showMenu = false;
      this.x = e.clientX;
      this.y = e.clientY;
      this.$nextTick(() => {
        this.showMenu = true;
      });
    },
    notification(message, color, timeout=5) {
      this.snackbarText = message
      this.snackbarColor = color
      this.snackbarTimeout = Number(timeout*1000)
      this.snackbar = true
    }
  }
}
</script>