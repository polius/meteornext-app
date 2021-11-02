<template>
  <div>
    <!---------------->
    <!-- NEW SERVER -->
    <!---------------->
    <v-dialog v-model="dialog" max-width="70%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-plus</v-icon>NEW SERVER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px">
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="white--text subtitle-1">SERVERS</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-text-field v-model="search" @input="onServerSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <v-card-text style="padding:0px;">
                      <Splitpanes style="height:62vh">
                        <Pane size="30" min-size="0" style="align-items:inherit">
                          <v-container fluid style="padding:0px;">
                            <v-row no-gutters style="height:calc(100% - 36px); overflow:auto;">
                              <v-progress-circular v-if="loading" indeterminate color="white" size="25" width="2" style="margin:12px;"></v-progress-circular>
                              <div v-else-if="items.length == 0" class="text-body-2" style="text-align:center; width:100%; display:grid; align-items:center">No servers to be selected</div>
                              <v-list v-else flat style="width:100%; padding:0px;">
                                <v-list-item-group mandatory multiple>
                                  <v-list-item v-for="item in items" :key="item.id" dense @click="onServerClick(item)" @contextmenu="$event.preventDefault()" style="max-height:20px;">
                                    <template>
                                      <v-list-item-action style="margin-right:15px">
                                        <v-checkbox dense :input-value="selected.includes(item.id)"></v-checkbox>
                                      </v-list-item-action>
                                      <v-list-item-content>
                                        <v-list-item-title>
                                          <v-chip small v-if="!item.active" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." label color="#EB5F5D" style="margin-right:10px">DISABLED</v-chip>
                                          <v-icon small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:6px; margin-bottom:2px">fas fa-server</v-icon>
                                          {{ item.name }}
                                        </v-list-item-title>
                                      </v-list-item-content>
                                    </template>
                                  </v-list-item>
                                </v-list-item-group>
                              </v-list>
                            </v-row>
                            <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
                              <v-btn @click="refresh" :loading="loading" :disabled="loading" text small title="Refresh Servers" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
                              <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                              <v-btn @click="selectAll" text small title="Select All" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-check-square</v-icon></v-btn>
                              <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                              <v-btn @click="deselectAll" text small title="Deselect All" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">far fa-square</v-icon></v-btn>
                              <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                            </v-row>
                          </v-container>
                        </Pane>
                        <Pane size="70" min-size="0" style="align-items:inherit; background-color:#484848; padding:1% 2% 1% 2%; overflow-y:auto;">
                          <v-container :style="`height:max(${height},100%); display:flex; align-items:center; justify-content:center;`">
                            <v-layout wrap>
                              <v-flex v-show="Object.keys(item).length == 0" xs12>
                                <div class="body-2" style="margin-top:1%; text-align:center;">Select a server to show the details</div>
                              </v-flex>
                              <v-flex ref="item" v-show="Object.keys(item).length != 0">
                                <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Server details</div>
                                <v-card>
                                  <v-card-text style="padding:15px">
                                    <v-row no-gutters>
                                      <v-col cols="6" style="padding-right:10px">
                                        <v-text-field v-model="item.name" readonly label="Name" required style="padding-top:8px"></v-text-field>
                                      </v-col>
                                      <v-col cols="6" style="padding-left:10px">
                                        <v-row no-gutters>
                                          <v-col cols="auto" style="margin-right:8px">
                                            <v-icon small :title="item.region_shared ? 'Shared' : 'Personal'" :color="item.region_shared ? '#EB5F5D' : 'warning'" style="margin-top:20px">{{ item.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                                          </v-col>
                                          <v-col>
                                            <v-text-field v-model="item.region" readonly label="Region" required style="padding-top:8px"></v-text-field>
                                          </v-col>
                                        </v-row>
                                      </v-col>
                                    </v-row>
                                    <!-- SQL -->
                                    <v-row no-gutters style="margin-bottom:5px">
                                      <v-col cols="8" style="padding-right:10px">
                                        <v-text-field v-model="item.engine" readonly label="Engine" required style="padding-top:0px" hide-details></v-text-field>
                                      </v-col>
                                      <v-col cols="4" style="padding-left:10px">
                                        <v-text-field v-model="item.version" readonly label="Version" required style="padding-top:0px" hide-details></v-text-field>
                                      </v-col>
                                    </v-row>
                                    <div v-if="!(inventory_secured && !owner && item.shared)" style="margin-top:25px; margin-bottom:10px">
                                      <v-row no-gutters>
                                        <v-col cols="8" style="padding-right:10px">
                                          <v-text-field v-model="item.hostname" readonly label="Hostname" required style="padding-top:0px"></v-text-field>
                                        </v-col>
                                        <v-col cols="4" style="padding-left:10px">
                                          <v-text-field v-model="item.port" readonly label="Port" required style="padding-top:0px"></v-text-field>
                                        </v-col>
                                      </v-row>
                                      <v-text-field v-model="item.username" readonly label="Username" required style="padding-top:0px"></v-text-field>
                                      <v-text-field v-model="item.password" readonly label="Password" :append-icon="sqlPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="sqlPassword ? 'text' : 'password'" @click:append="sqlPassword = !sqlPassword" style="padding-top:0px" hide-details></v-text-field>
                                    </div>
                                    <!-- SSL -->
                                    <v-card v-if="item.ssl" style="height:52px; margin-top:15px">
                                      <v-row no-gutters>
                                        <v-col cols="auto" style="display:flex; margin:15px">
                                          <v-icon color="#00b16a" style="font-size:20px">fas fa-key</v-icon>
                                        </v-col>
                                        <v-col>
                                          <div class="text-body-1" style="color:#00b16a; margin-top:15px">Using a SSL connection</div>
                                        </v-col>
                                      </v-row>
                                    </v-card>
                                    <!-- SSH -->
                                    <v-card v-if="item.ssh" style="height:52px; margin-top:15px">
                                      <v-row no-gutters>
                                        <v-col cols="auto" style="display:flex; margin:15px">
                                          <v-icon color="#2196f3" style="font-size:20px">fas fa-terminal</v-icon>
                                        </v-col>
                                        <v-col>
                                          <div class="text-body-1" style="color:#2196f3; margin-top:15px">Using a SSH connection</div>
                                        </v-col>
                                      </v-row>
                                    </v-card>
                                  </v-card-text>
                                </v-card>
                              </v-flex>
                            </v-layout>
                          </v-container>
                        </Pane>
                      </Splitpanes>
                    </v-card-text>
                  </v-card>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px">
                      <v-btn :disabled="selected.length == 0 || loading" :loading="loading" @click="newServerSubmit" color="#00b16a">Confirm</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn :disabled="loading" @click="dialog = false" color="#EF5354">Cancel</v-btn>
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
import axios from 'axios'
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      search: '',
      origin: [],
      items: [],
      selected: [],
      item: {},
      height: '100%',
      sqlPassword: false,
      sshPassword: false,
    }
  },
  components: { Splitpanes, Pane },
  computed: {
    ...mapFields([
      'servers',
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'sidebarSelected'
    ], { path: 'client/connection' }),
    owner: function() { return this.$store.getters['app/owner'] },
    inventory_secured: function() { return this.$store.getters['app/inventory_secured'] },
  },
  activated() {
    EventBus.$on('show-bottombar-servers-new', this.newServer)
  },
  watch: {
    dialog: function(val) {
      this.dialogOpened = val
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
      })
      this.deselectAll()
      this.getServers()
    },
  },
  methods: {
    getServers() {
      this.items = []
      this.loading = true
      axios.get('/client/servers/unassigned')
        .then((response) => {
          this.parseServers(response.data.servers)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false )
    },
    parseServers(data) {
      // Remove added servers
      const current = this.servers.reduce((acc, val) => { 'children' in val ? acc = acc.concat(val['children'].map(x => x.id)) : acc.push(val.id) ; return acc }, [])
      this.origin = data.filter(x => !current.includes(x.id))
      this.items = this.origin.slice(0)
    },
    onServerSearch(value) {
      if (value.length == 0) this.items = this.origin.slice(0)
      else this.items = this.origin.filter(x => x.name.toLowerCase().includes(value.toLowerCase()))
    },
    onServerClick(item) {
      const index = this.selected.findIndex(x => x == item.id)
      if (index > -1) this.selected.splice(index, 1)
      else this.selected.push(item.id)
      // Select the server to display
      if (this.selected.length == 0) this.item = {}
      else if (this.selected[this.selected.length - 1].id == item.id) this.item = JSON.parse(JSON.stringify(item))
      else this.item = this.origin.find(x => x.id == this.selected[this.selected.length - 1])
      // Calculate server component height
      this.$nextTick(() => {
        if (this.$refs.item !== undefined && this.$refs.item.clientHeight != 0) {
          this.height = this.$refs.item.clientHeight + 25 + 'px'
        }
      })
    },
    newServer() {
      this.dialog = true
    },
    newServerSubmit() {
      this.loading = true
      const payload = { 'servers': this.selected }
      axios.post('/client/servers', payload)
        .then((response) => {
          this.selected = []
          this.item = {}
          EventBus.$emit('send-notification', response.data.message, '#00b16a', 2)
          new Promise((resolve, reject) => EventBus.$emit('get-sidebar-servers', resolve, reject))
          .then(() => {
            const server = this.servers.find(x => !('children' in x) && x.id == payload.servers[payload.servers.length - 1])
            this.sidebarSelected = [server]
          })
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    refresh() {
      this.getServers()
    },
    selectAll() {
      this.selected = this.items.map(x => x.id)
      if (Object.keys(this.item).length == 0) this.item = JSON.parse(JSON.stringify(this.items[this.items.length - 1]))
    },
    deselectAll() {
      this.selected = []
      this.item = {}
    },
  }
}
</script>