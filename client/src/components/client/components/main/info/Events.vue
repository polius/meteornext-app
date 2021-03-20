<template>
  <div style="height:100%">
    <!------------>
    <!-- EVENTS -->
    <!------------>
    <div style="height:calc(100% - 36px)">
      <div style="width:100%; height:100%">
        <v-data-table :headers="infoHeaders.events" :items="infoItems.events" disable-sort hide-default-footer class="elevation-1" style="margin:10px; background-color:rgb(48,48,48);"></v-data-table>
        <div class="subtitle-2" style="padding:5px 15px 10px 15px; color:rgb(222,222,222);">EVENT DEFINITION</div>
        <div style="height:calc(100% - 118px);">
          <div id="infoEventsEditor" style="float:left"></div>
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
    ], { path: 'client/connection' }),
  },
  mounted () {
    // Register Event
    EventBus.$on('get-info-event', this.getInfo);

    // Init ACE Editor
    this.editor = ace.edit("infoEventsEditor", {
      mode: "ace/mode/mysql",
      theme: "ace/theme/monokai",
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
  methods: {
    getInfo() {
      if (this.infoConnection == this.sidebarSelected[0]['id']) return
      const payload = {
        connection: this.id + '-shared',
        server: this.server.id,
        database: this.database,
        object: 'event',
        name: this.sidebarSelected[0]['name']
      }
      axios.get('/client/info', { params: payload })
        .then((response) => {
          this.parseInfo(response.data)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    parseInfo(data) {
      var syntax = ''
      // Parse Info
      let info = JSON.parse(data.info)
      if (info.length == 0) {
        this.infoItems.events = []
        syntax = ''
        EventBus.$emit('send-notification', 'This event does not longer exist', 'error')
      }
      else {
        // Build Headers
        if (info[0]['type'] == 'ONE TIME') {
          this.infoHeaders.events = [
            { text: 'Name', value: 'name' },
            { text: 'Type', value: 'type' },
            { text: 'Execute At', value: 'execute_at' },
            { text: 'On Completion', value: 'on_completion' },
            { text: 'Definer', value: 'definer' },
            { text: 'Collation Connection', value: 'collation' },
            { text: 'Created', value: 'created' }
          ]
        }
        else if (info[0]['type'] == 'RECURRING') {
          this.infoHeaders.events = [
            { text: 'Name', value: 'name' },
            { text: 'Type', value: 'type' },
            { text: 'Interval Value', value: 'interval_value' },
            { text: 'Interval Field', value: 'interval_field' },
            { text: 'Starts', value: 'starts' },
            { text: 'Ends', value: 'ends' },
            { text: 'On Completion', value: 'on_completion' },
            { text: 'Definer', value: 'definer' },
            { text: 'Collation Connection', value: 'collation' },
            { text: 'Created', value: 'created' }
          ]
        }
        // Build Items
        this.infoItems.events = info
        syntax = sqlFormatter.format(info[0].syntax + ';', { reservedWordCase: 'upper'})
      }
      // Parse Syntax
      this.infoEditor.events = syntax
      this.editor.setValue(syntax, -1)
      this.editor.focus()
      // Store the current connection
      this.infoConnection = this.sidebarSelected[0]['id']
    },
  },
}
</script>