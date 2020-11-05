<template>
  <div style="height:100%">
    <!----------->
    <!-- VIEWS -->
    <!----------->
    <div style="height:calc(100% - 36px)">
      <div style="width:100%; height:100%">
        <v-data-table :headers="infoHeaders.views" :items="infoItems.views" disable-sort hide-default-footer class="elevation-1" style="margin:10px; background-color:rgb(48,48,48);"></v-data-table>
        <div class="subtitle-2" style="padding:5px 15px 10px 15px; color:rgb(222,222,222);">VIEW SYNTAX</div>
        <div style="height:calc(100% - 118px);">
          <div id="infoViewsEditor" style="float:left"></div>
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
  computed: {
    ...mapFields([
      'index',
      'infoHeaders',
      'infoItems',
      'infoEditor',
      'server',
      'database',
      'sidebarSelected',
    ], { path: 'client/connection' }),
  },
  mounted () {
    // Register Event
    EventBus.$on('get-info-view', this.getInfo);

    // Init ACE Editor
    this.editor = ace.edit("infoViewsEditor", {
      mode: "ace/mode/mysql",
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
      if (this.infoConnection == this.sidebarSelected[0]['id']) return
      const payload = {
        connection: this.index,
        server: this.server.id,
        database: this.database,
        object: 'view',
        name: this.sidebarSelected[0]['name']
      }
      axios.get('/client/info', { params: payload })
        .then((response) => {
          this.parseInfo(response.data)
        })
        .catch((error) => {
          console.log(error)
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, 'error')
        })
    },
    parseInfo(data) {
      var syntax = ''
      // Parse Info
      this.infoHeaders.views = [
        { text: 'Name', value: 'name' },
        { text: 'Check Option', value: 'check_option' },
        { text: 'Is Updatable', value: 'is_updatable' },
        { text: 'Definer', value: 'definer' },
        { text: 'Charset', value: 'charset' },
        { text: 'Collation', value: 'collation' }
      ]
      let info = JSON.parse(data.info)
      if (info.length == 0) {
        this.infoItems.views = []
        syntax = ''
        EventBus.$emit('send-notification', 'This view does not longer exist', 'error')
      }
      else {
        this.infoItems.views = info
        syntax = info[0].syntax + ';'
      }
      // Parse Syntax
      this.infoEditor.views = syntax
      this.editor.setValue(syntax, -1)
      this.editor.focus()
      // Store the current connection
      this.infoConnection = this.sidebarSelected[0]['id']
    },
  },
}
</script>