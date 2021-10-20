<template>
  <div style="height:100%">
    <!----------->
    <!-- VIEWS -->
    <!----------->
    <div style="height:calc(100% - 46px)">
      <div style="width:100%; height:100%">
        <v-data-table :headers="infoHeaders.views" :items="infoItems.views" disable-sort hide-default-footer class="elevation-1" style="margin:10px; background-color:rgb(48,48,48);"></v-data-table>
        <div class="subtitle-2" style="padding:5px 15px 10px 15px; color:rgb(222,222,222);">VIEW SYNTAX</div>
        <div style="height:calc(100% - 143px)">
          <div id="infoViewsEditor" style="float:left"></div>
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
      'infoConnection',
      'server',
      'database',
      'sidebarSelected',
      'sidebarLoadingObject',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('get-info-view', this.getInfo)
  },
  mounted() {
    // Init ACE Editor
    this.editor = ace.edit("infoViewsEditor", {
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
      this.editor.setValue(this.infoEditor.views, -1)
    }
  },
  methods: {
    getInfo(refresh) {
      if (!refresh && this.infoConnection == this.sidebarSelected[0]['id']) return
      this.sidebarLoadingObject = true
      const payload = {
        connection: this.id + '-shared',
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
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.sidebarLoadingObject = false)
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
        EventBus.$emit('send-notification', 'This view does not longer exist', '#EF5354')
      }
      else {
        this.infoItems.views = info
        syntax = sqlFormatter.format(info[0].syntax + ';', { reservedWordCase: 'upper'})
      }
      // Parse Syntax
      this.infoEditor.views = syntax
      this.editor.setValue(syntax, -1)
      this.editor.focus()
      // Store the current connection
      this.infoConnection = this.sidebarSelected[0]['id']
    },
    refresh() {
      this.getInfo(true)
    },
  },
}
</script>