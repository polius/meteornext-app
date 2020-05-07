<template>
  <div style="height: calc(100vh - 112px)">
    <Splitpanes>
      <Pane size="20" min-size="10">
        <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
          <v-treeview v-model="tree" :open="open" :items="items" activatable item-key="name" style="height:calc(100% - 58px); padding-top:5px; width:100%; overflow-y:auto;">
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
            <v-list>
              <v-list-item v-for="menuItem in menuItems" :key="menuItem" @click="clickAction">
                <v-list-item-title>{{menuItem}}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          <v-text-field v-model="search" label="Search" dense solo hide-details style="float:left; width:100%; padding:10px;"></v-text-field>
        </div>
      </Pane>
      <Pane size="80" min-size="10">
        <Splitpanes horizontal>
          <Pane size="100">
            <div id="editor"></div>
          </Pane>
          <Pane size="0" min-size="10">
            <v-data-table :headers="resultsHeaders" :items="resultsItems" :hide-default-footer="resultsItems.length < 11" class="elevation-1" style="height:100%; width:100%; border-radius:0px;">
            </v-data-table>
          </Pane>
        </Splitpanes>
      </Pane>
    </Splitpanes>
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
.container {
  padding: 0px;
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
}
.v-treeview-node__root {
  min-height:40px;
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
        },
        {
          name: "yarn.lock",
          file: "txt"
        }
      ],
      showMenu: false,
      x: 0,
      y: 0,
      menuItems: ["Preview Table", "Describe Table", "Backup", "Restore", "Refresh"],
      search: '',

      // ACE Editor
      editor: '',
      editorTools: null,

      // Results Table Data
      resultsHeaders: [],
      resultsItems: [],

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  components: { Splitpanes, Pane },
  mounted() {
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
    this.editor.session.setOptions({ tabSize: 4, useSoftTabs: false });

    var myList = [
      "/dev/sda1",
      "/dev/sda2"
    ]

    this.editorTools = ace.require("ace/ext/language_tools");
    var myCompleter = {
      identifierRegexps: [/[^\s]+/],
      getCompletions: function(editor, session, pos, prefix, callback) {
        callback(
          null,
          myList.filter(entry=>{
            return entry.includes(prefix);
          }).map(entry=>{
            return {
              value: entry
            };
          })
        );
      }
    }
    this.editorTools.addCompleter(myCompleter);
  },
  methods: {
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