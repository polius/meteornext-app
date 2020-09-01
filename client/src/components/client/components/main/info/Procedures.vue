<template>
  <div style="height:100%">
    <!---------------->
    <!-- PROCEDURES -->
    <!---------------->
    <div style="height:calc(100% - 36px)">
      <div style="width:100%; height:100%">
        <v-data-table :headers="infoHeaders.procedures" :items="infoItems.procedures" disable-sort hide-default-footer class="elevation-1" style="margin:10px; background-color:rgb(48,48,48);"></v-data-table>
        <div class="subtitle-2" style="padding:5px 15px 10px 15px; color:rgb(222,222,222);">PROCEDURE DEFINITION</div>
        <div style="height:calc(100% - 118px);">
          <div id="infoProceduresEditor" style="float:left"></div>
        </div>
      </div>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import EventBus from '../../../js/event-bus'
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
  components: {  },
  computed: {
    ...mapFields([
        'infoHeaders',
        'infoItems',
        'infoEditor',
        'server',
        'database',
        'treeviewSelected',
    ], { path: 'client/connection' }),
  },
  mounted () {
    // Register Event
    EventBus.$on('GET_INFO_PROCEDURE', this.getInfo);

    // Init ACE Editor
    this.editor = ace.edit("infoProceduresEditor", {
      mode: "ace/mode/sql",
      theme: "ace/theme/monokai",
      fontSize: 14,
      showPrintMargin: false,
      wrap: true,
      readOnly: true,
      showLineNumbers: false
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
  },
  methods: {
    getInfo() {
      const payload = {
        server: this.server.id,
        database: this.database,
        object: 'procedure',
        name: this.treeviewSelected['name']
      }
      axios.get('/client/info', { params: payload })
        .then((response) => {
          this.parseInfo(response.data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
        })
    },
    parseInfo(data) {
      var syntax = ''
      // Parse Info
      this.infoHeaders.procedures = [
        { text: 'Name', value: 'name' },
        { text: 'Deterministic', value: 'is_deterministic' },
        { text: 'Definer', value: 'definer' },
        { text: 'Charset', value: 'charset' },
        { text: 'Collation', value: 'collation' },
        { text: 'Created', value: 'created' }
      ]
      let info = JSON.parse(data.info)
      if (info.length == 0) {
        this.infoItems.functions = []
        syntax = ''
        EventBus.$emit('SEND_NOTIFICATION', 'This procedure does not longer exist', 'error')
      }
      else {
        this.infoItems.procedures = info
        syntax = info[0].syntax
      }
      // Parse Syntax
      if (syntax == null) {
        this.editor.getSession().setMode("ace/mode/text")
        syntax = 'Insufficient privileges to show the Procedure Definition.\n\nYou must be the user named in the routine DEFINER clause or have SELECT access to the mysql.proc table'
      }
      else this.editor.getSession().setMode("ace/mode/sql")
      this.infoEditor.procedures = syntax
      this.editor.setValue(syntax, -1)
      this.editor.focus()
    },
  },
}
</script>