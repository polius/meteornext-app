<template>
  <div id="rightsSyntax" style="float:left; height:calc(100% - 48px); width:100%"></div>
</template>

<script>
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

import ace from 'ace-builds';

export default {
  data() {
    return {
      editor: null,
    }
  },
  computed: {
    ...mapFields([
      'settings',
    ], { path: 'client/client' }),
    ...mapFields([
      'rights',
    ], { path: 'client/connection' }),
  },
  props: { tab: Number },
  activated() {
    EventBus.$on('reload-rights', this.reloadRights)
  },
  mounted() {
    // Init ACE Editor
    this.editor = ace.edit("rightsSyntax", {
      mode: "ace/mode/mysql",
      theme: "ace/theme/monokai",
      keyboardHandler: "ace/keyboard/vscode",
      fontSize: parseInt(this.settings['font_size']) || 14,
      showPrintMargin: false,
      wrap: false,
      readOnly: true,
      showLineNumbers: true
    });
    this.editor.commands.removeCommand('showSettingsMenu')
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
  },
  watch: {
    tab(value) {
      if (value == 4) this.reloadRights()
    }
  },
  methods: {
    reloadRights() {
      this.editor.setValue(this.rights['syntax'], -1)
    },
  }
}
</script>