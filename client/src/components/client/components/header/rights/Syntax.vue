<template>
  <div id="rightsSyntax" style="float:left; height:calc(100% - 48px); width:100%"></div>
</template>

<script>
import { mapFields } from '../../../js/map-fields'

import * as ace from 'ace-builds';
import 'ace-builds/webpack-resolver';
import 'ace-builds/src-noconflict/ext-language_tools';

export default {
  data() {
    return {
      editor: null
    }
  },
  props: { tab: Number },
  computed: {
    ...mapFields([
      'rights',
    ], { path: 'client/connection' }),
  },
  mounted() {
    // Init ACE Editor
    this.editor = ace.edit("rightsSyntax", {
      mode: "ace/mode/mysql",
      theme: "ace/theme/monokai",
      fontSize: 14,
      showPrintMargin: false,
      wrap: true,
      readOnly: true,
      showLineNumbers: true
    });
    this.editor.container.addEventListener("keydown", (e) => {
      // - Increase Font Size -
      if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
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
    this.editor.setValue(this.rights['syntax'], -1)
  },
  watch: {
    tab: function(value) {
      if (value == 4) this.editor.setValue(this.rights['syntax'], -1)
    }
  },
  methods: {

  }
}
</script>