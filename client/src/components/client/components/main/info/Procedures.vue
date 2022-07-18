<template>
  <div style="height:100%">
    <!---------------->
    <!-- PROCEDURES -->
    <!---------------->
    <div style="height:calc(100% - 46px)">
      <div style="width:100%; height:100%">
        <v-data-table :loading="loading" :headers="infoHeaders.procedures" :items="infoItems.procedures" disable-sort hide-default-footer class="elevation-1" style="margin:10px; background-color:rgb(48,48,48);" mobile-breakpoint="0"></v-data-table>
        <div class="subtitle-2" style="padding:5px 15px 10px 15px; color:rgb(222,222,222);">PROCEDURE DEFINITION</div>
        <div style="height:calc(100% - 143px)">
          <div id="infoProceduresEditor" style="float:left"></div>
        </div>
      </div>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-btn @click="refresh" text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

import ace from 'ace-builds';

import sqlFormatter from '@sqltools/formatter'

export default {
  data() {
    return {
      loading: false,
      editor: null
    }
  },
  computed: {
    ...mapFields([
      'settings',
      'currentConn',
    ], { path: 'client/client' }),
    ...mapFields([
      'index',
      'id',
      'infoHeaders',
      'infoItems',
      'infoEditor',
      'infoState',
      'server',
      'database',
      'sidebarSelected',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('get-info-procedure', this.getInfo)
  },
  mounted() {
    // Init ACE Editor
    this.editor = ace.edit("infoProceduresEditor", {
      mode: "ace/mode/mysql",
      theme: "ace/theme/monokai",
      keyboardHandler: "ace/keyboard/vscode",
      fontSize: parseInt(this.settings['font_size']) || 14,
      showPrintMargin: false,
      wrap: true,
      readOnly: true,
      showLineNumbers: false
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
    currentConn() {
      this.editor.setValue(this.infoEditor.procedures, -1)
    }
  },
  methods: {
    getInfo(refresh) {
      this.editor.setValue(this.infoEditor.procedures, -1)
      if (!refresh && this.infoState == (this.database + '|' + this.sidebarSelected[0]['id'])) return
      this.loading = true
      const payload = {
        connection: this.id + '-shared',
        server: this.server.id,
        database: this.database,
        object: 'procedure',
        name: this.sidebarSelected[0]['name']
      }
      axios.get('/client/info', { params: payload })
        .then((response) => {
          this.parseInfo(response.data)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
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
        EventBus.$emit('send-notification', 'This procedure does not longer exist', '#EF5354')
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
      else {
        this.editor.getSession().setMode("ace/mode/mysql")
        syntax = sqlFormatter.format(syntax + ';', { reservedWordCase: 'upper'})
      }
      this.infoEditor.procedures = syntax
      this.editor.setValue(syntax, -1)
      this.editor.focus()
      // Store the current info state
      this.infoState = this.database + '|' + this.sidebarSelected[0]['id']
    },
    refresh() {
      this.getInfo(true)
    },
  },
}
</script>