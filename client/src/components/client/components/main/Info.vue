<template>
  <div style="height:100%">
    <!---------->
    <!-- INFO -->
    <!---------->
    <div style="height:calc(100% - 36px)">
      <div style="width:100%; height:100%">
        <v-data-table :headers="infoHeaders" :items="infoItems" disable-sort hide-default-footer class="elevation-1" style="margin:10px; background-color:rgb(48,48,48);"></v-data-table>
        <div class="subtitle-2" style="padding:5px 15px 10px 15px; color:rgb(222,222,222);">TABLE SYNTAX</div>
        <div style="height:calc(100% - 118px);">
          <div id="infoEditor" style="float:left"></div>
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
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import * as ace from 'ace-builds';
import 'ace-builds/webpack-resolver';
import 'ace-builds/src-noconflict/ext-language_tools';

export default {
  data() {
    return {
    }
  },
  components: {  },
  computed: {
    ...mapFields([
        'infoHeaders',
        'infoItems',
        'server',
        'database',
        'treeviewSelected',
        'infoEditor',
    ], { path: 'client/connection' }),
  },
  mounted () {
    // Register Event
    EventBus.$on('GET_INFO', this.getInfo);

    // Init ACE Editor
    this.infoEditor = ace.edit("infoEditor", {
      mode: "ace/mode/sql",
      theme: "ace/theme/monokai",
      fontSize: 14,
      showPrintMargin: false,
      wrap: true,
      readOnly: true,
      showLineNumbers: false
    });
    this.infoEditor.container.addEventListener("keydown", (e) => {
      // - Increase Font Size -
      if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
        let size = parseInt(this.infoEditor.getFontSize(), 10) || 12
        this.infoEditor.setFontSize(size + 1)
        e.preventDefault()
      }
      // - Decrease Font Size -
      else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
        let size = parseInt(this.infoEditor.getFontSize(), 10) || 12
        this.infoEditor.setFontSize(Math.max(size - 1 || 1))
        e.preventDefault()
      }
    }, false);
  },
  methods: {
    getInfo() {
      const payload = {
        server: this.server.id,
        database: this.database,
        table: this.treeviewSelected['name']
      }
      axios.get('/client/info', { params: payload })
        .then((response) => {
          this.parseInfo(response.data)
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
    },
    parseInfo(data) {
      // Parse Info
      this.infoHeaders = [
        { text: 'Engine', value: 'engine' },
        { text: 'Row format', value: 'row_format' },
        { text: 'Rows', value: 'table_rows' },
        { text: 'Data size', value: 'data_length' },
        { text: 'Index size', value: 'index_length' },
        { text: 'Total size', value: 'total_length' },
        { text: 'Collation', value: 'table_collation' },
        { text: 'Created', value: 'create_time' },
        { text: 'Updated', value: 'update_time' }
      ]
      let info = JSON.parse(data.info)
      info['total_length'] = this.parseBytes(info.data_length + info.index_length)
      info.data_length = this.parseBytes(info.data_length)
      info.index_length = this.parseBytes(info.index_length)
      info.create_time = (info.create_time == null) ? 'Not available' : info.create_time
      info.update_time = (info.update_time == null) ? 'Not available' : info.update_time
      this.infoItems = [info]

      // Parse Syntax
      let syntax = JSON.parse(data.syntax)
      this.infoEditor.setValue(syntax, -1)
      this.infoEditor.focus()
    },
    parseBytes(value) {
      if (value/1024 < 1) return value + ' B'
      else if (value/1024/1024 < 1) return value/1024 + 'KB'
      else if (value/1024/1024/1024 < 1) return value/1024/1024 + 'MB'
      else if (value/1024/1024/1024/1024 < 1) return value/1024/1024/1024 + 'GB'
      else return value/1024/1024/1024/1024 + 'TB' 
    },
  },
}
</script>