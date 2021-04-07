<template>
  <div>
    <v-dialog ref="savedDialog" v-model="dialog" @keydown="onKeyDown" max-width="80%" eager>
      <v-card>
        <v-toolbar flat dense color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:4px">fas fa-star</v-icon>SAVED QUERIES</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn :disabled="selected.length != 1 || saveButtonDisabled" :loading="loading" @click="editSaved" color="primary" style="margin-right:10px;">Save</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <Splitpanes @ready="onSplitPaneReady" style="height:80vh">
                  <Pane size="20" min-size="0" style="align-items:inherit">
                    <v-container fluid style="padding:0px;">
                      <v-row ref="list" no-gutters style="height:calc(100% - 93px); overflow:auto;">
                        <v-list style="width:100%; padding:0px;">
                          <v-list-item-group v-model="selected" mandatory multiple>
                            <v-list-item v-for="(item, i) in items" :key="i" dense :ref="'saved' + i" @click="onListClick($event, i)" @contextmenu="onListRightClick">
                              <v-list-item-content><v-list-item-title v-text="item.name"></v-list-item-title></v-list-item-content>
                            </v-list-item>
                          </v-list-item-group>
                        </v-list>
                      </v-row>
                      <v-row no-gutters>
                        <v-text-field ref="search" v-model="search" label="Search" @input="onSavedSearch" dense solo hide-details height="38px" style="float:left; width:100%; padding:10px;"></v-text-field>
                      </v-row>
                      <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
                        <v-btn @click="addSaved" text small title="New Saved Query" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
                        <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                        <v-btn @click="confirmDialog = true" :disabled="selected.length == 0" text small title="Delete Save Query" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
                        <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                      </v-row>
                    </v-container>
                  </Pane>
                  <Pane size="80" min-size="0" style="background-color:#484848">
                    <div style="height:100%; width:100%">
                      <v-text-field ref="name" @input="checkValues" :disabled="selected.length != 1" v-model="name" outlined dense label="Name" hide-details style="margin:10px"></v-text-field>
                      <div style="height:calc(100% - 60px)">
                        <div id="savedEditor" style="float:left; width:100%; height:100%"></div>
                      </div>
                    </div>
                  </Pane>
                </Splitpanes>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------->
    <!-- CONFIRM DIALOG -->
    <!-------------------->
    <v-dialog v-model="confirmDialog" persistent max-width="60%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">Remove selected saved queries?</div>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div class="body-1" style="font-weight:300; font-size:1.05rem!important;">Are you sure you want to remove all selected saved queries? This action cannot be undone.</div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="deleteSaved" color="#00b16a">Confirm</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="confirmDialog = false" color="error">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped src="@/styles/splitPanes.css"></style>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import ace from 'ace-builds';

import axios from 'axios'

export default {
  data() {
    return {
      loading: false,
      dialog: false,
      confirmDialog: false,
      origin: [],
      items: [],
      selected: [],
      search: '',
      name: '',
      editor: null,
      saveButtonDisabled: true,
    }
  },
  components: { Splitpanes, Pane },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-saved', this.showDialog);
  },
  watch: {
    dialog: function(value) {
      this.dialogOpened = value
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 7}
        this.headerTab = tab[this.headerTabSelected]
      }
    },
  },
  methods: {
    showDialog() {
      this.dialog = true
      this.selected = (this.items.length > 0) ? [0]: []
      this.getSaved()
    },
    getSaved() {
      // Get Saved queries
      axios.get('/client/saved')
        .then((response) => {
          this.origin = response.data.saved
          this.items = response.data.saved
          if (this.items.length == 0) this.addSaved()
          else {
            this.selected = [0]
            let current = this.items[0]
            this.name = current['name']
            this.editor.setValue(current['query'], -1)
            requestAnimationFrame(() => {
              if (typeof this.$refs.search !== 'undefined') this.$refs.search.focus()
            })
          }
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    addSaved() {      
      const payload = {'name': 'New Saved Query', 'query': ''}
      axios.post('/client/saved', payload)
        .then((response) => {
          this.items.push({'id': response.data.data, 'name': payload['name'], 'query': payload['query']})
          this.selected = [this.items.length - 1]
          this.name = payload['name']
          this.editor.setValue(payload['query'], -1)
          this.$nextTick(() => {
            this.$refs.list.scrollTop = this.$refs.list.scrollHeight
            this.$refs.name.focus()
            this.$refs.name.$el.querySelector('input').setSelectionRange(0, this.name.length)
          })
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    editSaved() {
      this.loading = true
      let curr = this.selected[0]
      const payload = {'id': this.items[curr]['id'], 'name': this.name, 'query': this.editor.getValue()}
      axios.put('/client/saved', payload)
        .then(() => {
          this.items[curr]['name'] = payload['name']
          this.items[curr]['query'] = payload['query']
          this.saveButtonDisabled = true
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    deleteSaved() {
      this.loading = true
      const payload = this.selected.reduce((acc, item) => { acc.push(this.items[item]['id']); return acc }, [])
      axios.delete('/client/saved', { data: payload })
        .then(() => {
          if (payload.length < this.items.length) {
            let sel = (this.selected[0] - 1 < 0) ? this.selected[this.selected.length-1] + 1 : this.selected[0] - 1
            this.$refs['saved' + sel][0].$el.focus()
            this.name = this.items[sel]['name']
            this.editor.setValue(this.items[sel]['query'], -1)
          }
          else {
            this.name = ''
            this.editor.setValue('', -1)
          }
          this.selected = []
          this.items = this.items.filter(item => !payload.includes(item.id))
          this.confirmDialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    onSplitPaneReady() {
      // Init ACE Editor
      this.editor = ace.edit("savedEditor", {
        mode: "ace/mode/mysql",
        theme: "ace/theme/monokai",
        fontSize: 14,
        showPrintMargin: false,
        wrap: true,
        showLineNumbers: true
      });
      this.editor.on("changeSelection", this.checkValues)
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
    onKeyDown(event) {
      if (!this.dialog) return
      if (event.target.tagName == 'DIV' && this.items.length > 0) {
        if (event.code == 'ArrowDown') {
          if (event.shiftKey) {
            let last = this.selected.slice(-1)[0]
            if ((last + 1) == this.items.length) return
            if (this.selected.includes(last+1)) this.selected.pop()
            else this.selected.push((last + 1))
            this.$refs['saved' + (last + 1)][0].$el.focus()
          }
          else {
            let max = Math.max(...this.selected)
            let newVal = ((max + 1) < this.items.length) ? max + 1 : max
            this.selected = [newVal]
            this.$refs['saved' + newVal][0].$el.focus()
          }
        }
        else if (event.code == 'ArrowUp') {
          if (event.shiftKey) {
            let last = this.selected.slice(-1)[0]
            if (last == 0) return
            if (this.selected.includes(last-1)) this.selected.pop()
            else this.selected.push((last - 1))
            this.$refs['saved' + (last - 1)][0].$el.focus()
          }
          else {
            let min = Math.min(...this.selected)
            let newVal = (min > 0) ? min - 1 : min
            this.selected = [newVal]
            this.$refs['saved' + newVal][0].$el.focus()
          }
        }
        if (['ArrowDown','ArrowUp'].includes(event.code)) {
          if (this.selected.length > 0) {
            let current = this.items[this.selected[this.selected.length - 1]]
            this.name = current['name']
            this.editor.setValue(current['query'], -1)
          }
          event.preventDefault()
        }
      }
    },
    onListClick(event, value) {
      var selected = this.selected
      this.$nextTick(() => {
        if (event.shiftKey && !event.ctrlKey && !event.metaKey) {
          this.selected = []
          if (selected[0] < value) for (let i = selected[0]; i <= value; ++i) this.selected.push(i)
          else for (let i = selected[0]; i >= value; i--) this.selected.push(i)
        }
        else if (!event.ctrlKey && !event.metaKey) this.selected = [value]
        if (selected.includes(value)) this.$refs['saved' + value][0].$el.blur()
        else this.$refs['saved' + value][0].$el.focus()
        if (this.selected.length > 0) {
          let current = this.items[this.selected[this.selected.length - 1]]
          this.name = current['name']
          this.editor.setValue(current['query'], -1)
        }
      })
    },
    onListRightClick(event) {
      event.preventDefault()
    },
    onSavedSearch(value) {
      if (value.length == 0) this.items = this.origin.slice(0)
      else this.items = this.origin.filter(x => x.name.toLowerCase().includes(value.toLowerCase()))
    },
    checkValues() {
      if (this.items[this.selected[0]] == undefined) return
      if (this.items[this.selected[0]]['name'] == this.name && this.items[this.selected[0]]['query'] == this.editor.getValue()) this.saveButtonDisabled = true
      else this.saveButtonDisabled = false
    },
  }
}
</script>