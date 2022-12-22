<template>
  <div style="height:100%">
    <!------------>
    <!-- TABLES -->
    <!------------>
    <div style="height:calc(100% - 46px)">
      <div style="width:100%; height:100%">
        <v-data-table :loading="loading" :headers="infoHeaders.tables" :items="infoItems.tables" disable-sort hide-default-footer class="elevation-1" style="margin:10px; background-color:rgb(48,48,48);" mobile-breakpoint="0"></v-data-table>
        <div class="subtitle-2" style="padding:5px 15px 10px 15px; color:rgb(222,222,222);">TABLE SYNTAX</div>
        <div style="height:calc(100% - 143px)">
          <div id="infoTablesEditor" style="float:left"></div>
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
    EventBus.$on('get-info-table', this.getInfo)
  },
  mounted() {
    // Init ACE Editor
    this.editor = ace.edit("infoTablesEditor", {
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
      this.editor.setValue(this.infoEditor.tables, -1)
    }
  },
  methods: {
    getInfo(refresh) {
      this.editor.setValue(this.infoEditor.tables, -1)
      if (!refresh && this.infoState == (this.database + '|' + this.sidebarSelected[0]['id'])) return
      this.loading = true
      const payload = {
        connection: this.id + '-shared',
        server: this.server.id,
        database: this.database,
        object: 'table',
        name: this.sidebarSelected[0]['name'].replaceAll('`','``')
      }
      axios.get('/client/info', { params: payload })
        .then((response) => {
          this.parseInfo(response.data)
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    parseInfo(data) {
      var syntax = ''
      // Parse Info
      this.infoHeaders.tables = [
        { text: 'Name', value: 'name'},
        { text: 'Engine', value: 'engine' },
        { text: 'Row Format', value: 'row_format' },
        { text: 'Rows', value: 'rows' },
        { text: 'Data Length', value: 'data_length' },
        { text: 'Index Length', value: 'index_length' },
        { text: 'Total Length', value: 'total_length' },
        { text: 'Collation', value: 'collation' },
        { text: 'Created', value: 'created' },
        { text: 'Modified', value: 'modified' }
      ]
      let info = JSON.parse(data.info)
      if (info.length == 0) {
        this.infoItems.tables = []
        syntax = ''
        EventBus.$emit('send-notification', 'This table does not longer exist', '#EF5354')
      }
      else {
        info = info[0]
        info['total_length'] = this.parseBytes(info.data_length + info.index_length)
        info.data_length = this.parseBytes(info.data_length)
        info.index_length = this.parseBytes(info.index_length)
        info.create_time = (info.create_time == null) ? 'Not available' : info.create_time
        info.update_time = (info.update_time == null) ? 'Not available' : info.update_time
        this.infoItems.tables = [info]
        syntax = sqlFormatter.format(info.syntax + ';', { reservedWordCase: 'upper'})
      }
      // Parse Syntax
      this.infoEditor.tables = syntax
      this.editor.setValue(syntax, -1)
      this.editor.focus()
      // Store the current info state
      this.infoState = this.database + '|' + this.sidebarSelected[0]['id']
    },
    refresh() {
      this.getInfo(true)
    },
    parseBytes(value) {
      if (value/1024 < 1) return value + ' B'
      else if (value/1024/1024 < 1) return (value/1024).toFixed(2) + ' KB'
      else if (value/1024/1024/1024 < 1) return (value/1024/1024).toFixed(2) + ' MB'
      else if (value/1024/1024/1024/1024 < 1) return (value/1024/1024/1024).toFixed(2) + ' GB'
      else return (value/1024/1024/1024/1024).toFixed(2) + ' TB'
    },
  },
}
</script>