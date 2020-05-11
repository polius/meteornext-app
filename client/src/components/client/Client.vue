<template>
  <div style="margin: -12px;">
    <div ref="masterDiv" style="height: calc(100vh - 145px);">
      <Splitpanes>
        <Pane size="20" min-size="0">
          <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
            <v-select solo :items="databaseItems" label="Database" hide-details background-color="#303030" style="padding: 10px 10px 10px 10px;"></v-select>
            <div class="subtitle-2" style="padding-left:10px; padding-top:10px; color:rgb(222,222,222);">SERVERS</div>
            <v-treeview @contextmenu="show" v-model="tree" :open="open" :items="items" activatable item-key="name" class="clear_shadow" style="height:calc(100% - 160px); padding-top:7px; width:100%; overflow-y:auto;">
              <template v-slot:label="{item, open}">        
                <v-btn text @contextmenu="show" style="font-size:14px; text-transform:none; font-weight:400; width:100%; justify-content:left; padding:0px;"> 
                  <!--button icon-->
                  <v-icon v-if="!item.file" small style="padding:10px;">
                    {{ open ? 'mdi-folder-open' : 'mdi-folder' }}
                  </v-icon>
                  <v-icon v-else small style="padding:10px;">
                    {{ files[item.file] }}
                  </v-icon>
                  <!--button text-->
                  {{item.name}}                  
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
            <v-text-field v-model="search" label="Search" dense solo hide-details style="float:left; width:100%; padding:10px;"></v-text-field>
          </div>
        </Pane>
        <Pane size="80" min-size="0">
          <Splitpanes horizontal @ready="initAce()" @resize="resize($event)">
            <Pane size="100">
              <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
                <v-tabs show-arrows dense background-color="#303030" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2" style="max-width:calc(100% - 97px); float:left;">
                  <v-tabs-slider></v-tabs-slider>
                  <v-tab v-for="t in connections" :key="t" style="padding:0px 10px 0px 0px;">
                    <span class="pl-2 pr-2"><v-btn small icon @click="removeConnection(t)" style="margin-right:10px;"><v-icon x-small style="padding-bottom:1px;">fas fa-times</v-icon></v-btn>{{ t }}</span>
                  </v-tab>
                  <v-btn text @click="newConnection()" style="height:100%; font-size:16px;">+</v-btn>
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
    <div style="width:100%; padding-top:5px; padding-left:20px; padding-right:20px; border-top:2px solid rgba(37, 37, 37, 0.5);">
      <div class="body-2" style="float:left; width:calc(100vw - 180px); text-align:center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">5 rows affected</div>
      <div class="body-2" style="float:right; text-align:right;">0.046s elapsed</div>
    </div>
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
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import * as ace from 'ace-builds';
import 'ace-builds/webpack-resolver';
import 'ace-builds/src-noconflict/ext-language_tools';

export default {
  data() {
    return {
      // Connections
      connections: ['Connection 1', 'Connection 2'],
      // Tabs
      tabs: 0,
      databaseItems: ['ilf_admin','ilf_palzina_km_en_tmpl_edit'],

      // Servers Tree View
      open: ["public"],
      files: {
        html: "mdi-language-html5",
        js: "mdi-nodejs",
        json: "mdi-json",
        md: "mdi-markdown",
        pdf: "mdi-file-pdf",
        png: "mdi-file-image",
        txt: "mdi-file-document-outline",
        xls: "mdi-file-excel"
      },
      tree: [],
      items: [
        {
          name: ".git"
        },
        {
          name: "node_modules"
        },
        {
          name: "public",
          children: [
            {
              name: "static",
              children: [
                {
                  name: "logo.png",
                  file: "png"
                }
              ]
            },
            {
              name: "favicon.ico",
              file: "png"
            },
            {
              name: "index.html",
              file: "html"
            }
          ]
        },
        {
          name: ".gitignore",
          file: "txt"
        },
        {
          name: "babel.config.js",
          file: "js"
        },
        {
          name: "package.json",
          file: "json"
        },
        {
          name: "README.md",
          file: "md"
        },
        {
          name: "vue.config.js",
          file: "js"
        }
      ],
      showMenu: false,
      x: 0,
      y: 0,
      menuItems: ["Structure", "Content", "Relations", "Table Info", "Delete", "Truncate", "Duplicate", "Rename"],
      search: '',

      // ACE Editor
      editor: null,
      editorTools: null,

      // Results Table Data
      resultsHeight: 0,
      resultsHeaders: [
        { text: 'Dessert (100g serving)', value: 'name' },
        { text: 'Calories', value: 'calories' },
        { text: 'Fat (g)', value: 'fat' },
        { text: 'Carbs (g)', value: 'carbs' },
        { text: 'Protein (g)', value: 'protein' },
        { text: 'Iron (%)', value: 'iron' }
      ],
      resultsItems: [
        {
            name: 'Frozen Yogurt',
            calories: 159,
            fat: 6.0,
            carbs: 24,
            protein: 4.0,
            iron: '1%',
          },
          {
            name: 'Ice cream sandwich',
            calories: 237,
            fat: 9.0,
            carbs: 37,
            protein: 4.3,
            iron: '1%',
          },
          {
            name: 'Eclair',
            calories: 262,
            fat: 16.0,
            carbs: 23,
            protein: 6.0,
            iron: '7%',
          },
          {
            name: 'Cupcake',
            calories: 305,
            fat: 3.7,
            carbs: 67,
            protein: 4.3,
            iron: '8%',
          },
          {
            name: 'Gingerbread',
            calories: 356,
            fat: 16.0,
            carbs: 49,
            protein: 3.9,
            iron: '16%',
          },
          {
            name: 'Jelly bean',
            calories: 375,
            fat: 0.0,
            carbs: 94,
            protein: 0.0,
            iron: '0%',
          },
          {
            name: 'Lollipop',
            calories: 392,
            fat: 0.2,
            carbs: 98,
            protein: 0,
            iron: '2%',
          },
          {
            name: 'Honeycomb',
            calories: 408,
            fat: 3.2,
            carbs: 87,
            protein: 6.5,
            iron: '45%',
          },
          {
            name: 'Donut',
            calories: 452,
            fat: 25.0,
            carbs: 51,
            protein: 4.9,
            iron: '22%',
          },
          {
            name: 'KitKat',
            calories: 518,
            fat: 26.0,
            carbs: 65,
            protein: 7,
            iron: '6%',
          }
      ],

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  components: { Splitpanes, Pane },
  mounted() {

  },
  methods: {
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
    }
  }
}
</script>