<template>
  <div style="margin: -12px;">
    <div ref="masterDiv" style="height: calc(100vh - 145px);">
      <Splitpanes>
        <Pane size="20" min-size="0">
          <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
            <v-select @change="getTables" solo :disabled="databaseItems.length == 0" :items="databaseItems" label="Database" hide-details background-color="#303030" style="padding: 10px 10px 10px 10px;"></v-select>
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
            <Pane size="100">
              <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
                <v-tabs show-arrows dense background-color="#303030" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2" style="max-width:calc(100% - 97px); float:left;">
                  <v-tabs-slider></v-tabs-slider>
                  <v-tab v-for="t in connections" :key="t" :title="t" style="padding:0px 10px 0px 0px;">
                    <span class="pl-2 pr-2"><v-btn title="Close Connection" small icon @click="removeConnection(t)" style="margin-right:10px;"><v-icon x-small style="padding-bottom:1px;">fas fa-times</v-icon></v-btn>{{ t }}</span>
                  </v-tab>
                  <v-divider class="mx-3" inset vertical></v-divider>
                  <v-btn text title="New Connection" @click="newConnection()" style="height:100%; font-size:16px;">+</v-btn>
                  <v-divider class="mx-3" inset vertical></v-divider>
                </v-tabs>
                <v-btn style="margin:6px;" title="Execute Query"><v-icon small style="padding-right:10px;">fas fa-bolt</v-icon>Run</v-btn>
                <div id="editor" style="float:left"></div>
              </div>
            </Pane>
            <Pane size="0" min-size="0">
              <v-data-table :headers="resultsHeaders" :items="resultsItems" :footer-props="{'items-per-page-options': [10, 100, 1000, -1]}" :items-per-page="100" :hide-default-footer="resultsItems.length == 0" class="elevation-1" :height="resultsHeight + 'px'" fixed-header style="width:100%; border-radius:0px; background-color:#303030; overflow-y: auto;">
              </v-data-table>
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
</template>

<style>
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
  min-height:40px;
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

export default {
  data() {
    return {
      // State vars
      serverSelected: null,
      loadingServer: false,

      // Database Selector
      databaseItems: [],

      // Servers Tree View
      treeviewMode: 'servers',
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
      treeviewSearch: '',

      // Menu (right click)
      showMenu: false,
      x: 0,
      y: 0,
      menuItems: ["Rename", "Truncate", "Delete", "Duplicate", "Export"],

      // Connections
      tabs: 0,
      connections: ['Connection 1'],

      // ACE Editor
      editor: null,
      editorTools: null,

      // Results Table Data
      resultsHeight: 0,
      resultsHeaders: [],
      resultsItems: [],

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(5000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  components: { Splitpanes, Pane },
  created() {
    this.getServers()
  },
  methods: {
    doubleClick(item) {
      if (this.treeviewMode == 'servers') this.getDatabases(item.id)
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
        if (found) servers[j]['children'].push({ id: data[i]['server_id'], name: data[i]['server_name'], type: data[i]['server_engine'] })
        else servers.push({ id: 'r' + data[i]['region_id'], name: data[i]['region_name'], children: [{ id: data[i]['server_id'], name: data[i]['server_name'], type: data[i]['server_engine'] }] })
      }
      this.treeviewItems = servers.slice(0)
    },
    getDatabases(server_id) {
      // Select Server
      this.treeview = [server_id]
      this.loadingServer = true
      this.serverSelected = server_id

      // Retrieve Databases
      axios.get('/client/databases', { params: { server_id: server_id } })
        .then((response) => {
          this.treeview = []
          this.treeviewItems = []
          this.treeviewMode = 'tables'
          this.databaseItems = response.data.data
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
      axios.get('/client/tables', { params: { server_id: this.serverSelected, database_name: database } })
        .then((response) => {
          this.parseTables(response.data.data)
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
      this.connections.push("New")
      this.tabs = this.connections.length - 1
    },
    removeConnection(i) {
      var index = this.connections.indexOf(i)
      this.connections.splice(index, 1)
    },
    initAce() {
      // Create Editor
      this.editor = ace.edit("editor", {
        mode: "ace/mode/sql",
        theme: "ace/theme/monokai",
        fontSize: 14,
        showPrintMargin: false,
        wrap: true,
        autoScrollEditorIntoView: true,
        enableBasicAutocompletion: true,
        enableLiveAutocompletion: true,
        enableSnippets: false
      });
      this.editor.session.setOptions({ tabSize: 4, useSoftTabs: false })

      var myList = [
        "/dev/sda1",
        "/dev/sda2"
      ]

      this.editorTools = ace.require("ace/ext/language_tools")
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
      this.editorTools.addCompleter(myCompleter)
      this.editor.renderer.on('afterRender', this.resize);
    },
    resize(event) {
      // Resize Results Data Table
      if (typeof event !== 'undefined' && event.length > 0) this.resultsHeight = this.$refs.masterDiv.clientHeight * event[1].size / 100 - 62

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