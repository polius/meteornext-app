<template>
  <div style="height: calc(100vh - 112px)">
    <Splitpanes>
      <Pane size="20" min-size="10">
        <span>1</span>
      </Pane>
      <Pane size="80" min-size="10">
        <Splitpanes horizontal>
          <Pane size="90">
            <!-- <span>2</span> -->
            <div id="editor" style="height:100vh"></div>
          </Pane>
          <Pane size="10" min-size="10">
            <span>3</span>
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
  min-width: 3px;
}
.splitpanes--horizontal > .splitpanes__splitter {
  min-height: 3px;
}
.ace_editor {
  margin: auto;
  height: 100%;
  width: 100%;
}
#editor {
  height: 100%;
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
      // ACE Editor
      editor: '',
      editorTools: null,

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
    
  }
}
</script>