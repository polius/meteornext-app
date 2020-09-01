<template>
  <div style="height:100%">
    <!------------>
    <!-- TABLES -->
    <!------------>
    <div style="height:calc(100% - 36px)">
      <div style="width:100%; height:100%">
        <v-data-table :headers="infoHeaders.tables" :items="infoItems.tables" disable-sort hide-default-footer class="elevation-1" style="margin:10px; background-color:rgb(48,48,48);"></v-data-table>
        <div class="subtitle-2" style="padding:5px 15px 10px 15px; color:rgb(222,222,222);">TABLE SYNTAX</div>
        <div style="height:calc(100% - 118px);">
          <div id="infoTablesEditor" style="float:left"></div>
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
    EventBus.$on('GET_INFO_TABLE', this.getInfo);

    // Init ACE Editor
    this.editor = ace.edit("infoTablesEditor", {
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
        object: 'table',
        name: this.treeviewSelected['name']
      }
      axios.get('/client/info', { params: payload })
        .then((response) => {
          this.parseInfo(response.data)
        })
        .catch((error) => {
          console.log(error)
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
        })
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
        EventBus.$emit('SEND_NOTIFICATION', 'This table does not longer exist', 'error')
      }
      else {
        info = info[0]
        info['total_length'] = this.parseBytes(info.data_length + info.index_length)
        info.data_length = this.parseBytes(info.data_length)
        info.index_length = this.parseBytes(info.index_length)
        info.create_time = (info.create_time == null) ? 'Not available' : info.create_time
        info.update_time = (info.update_time == null) ? 'Not available' : info.update_time
        this.infoItems.tables = [info]
        syntax = info.syntax
      }
      // Parse Syntax
      this.infoEditor.tables = syntax
      this.editor.setValue(syntax, -1)
      this.editor.focus()
    },
    parseBytes(value) {
      if (value/1024 < 1) return value + ' B'
      else if (value/1024/1024 < 1) return value/1024 + ' KB'
      else if (value/1024/1024/1024 < 1) return value/1024/1024 + ' MB'
      else if (value/1024/1024/1024/1024 < 1) return value/1024/1024/1024 + ' GB'
      else return value/1024/1024/1024/1024 + ' TB' 
    },
  },
}
</script>