<template>
  <v-container fluid style="padding:0px;">
    <v-row ref="list" no-gutters style="height:calc(100% - 36px); overflow:auto;">
      <v-text-field ref="search" :disabled="rights['sidebar'].length == 0" v-model="rightsSidebarSearch" placeholder="Search" autofocus dense solo hide-details height="42px" style="padding:5px 5px 5px;"></v-text-field>
      <v-treeview :active.sync="rightsSidebarSelected" item-key="id" :open.sync="rightsSidebarOpened" :items="rights['sidebar']" :search="rightsSidebarSearch" :activatable="!rightsLoading" open-on-click transition class="clear_shadow" style="height:calc(100% - 56px); width:100%; overflow-y:auto;">
        <template v-slot:label="{item, active}">
          <v-btn @click="sidebarClick($event, item, active)" @contextmenu="onRightClick" text :style="`font-size:14px; text-transform:none; font-weight:400; width:100%; justify-content:left; padding-left:10px; ${rightsLoading ? 'cursor:not-allowed' : 'cursor:pointer'}`">
            <v-icon v-if="'children' in item" small style="padding-right:10px">fas fa-user</v-icon>
            {{ item.name }}
            <v-spacer></v-spacer>
            <v-progress-circular v-if="rightsLoading && item.id == rightsSidebarClicked" indeterminate size="16" width="2" color="white"></v-progress-circular>
          </v-btn>
        </template>
      </v-treeview>
    </v-row>
    <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
      <v-btn :disabled="rightsLoading" @click="refreshRights" text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="rightsLoading" @click="addRight" text small title="New User Right" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="Object.keys(rightsSelected).length == 0 || rightsLoading" @click="removeRight" text small title="Delete User Right" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="Object.keys(rightsSelected).length == 0 || rightsLoading" @click="cloneRight" text small title="Clone User Right" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-clone</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
    </v-row>

    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="sidebarDialog" persistent max-width="60%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">Delete user</div>
              <v-flex xs12>
                <v-form style="margin-top:10px; margin-bottom:15px;">
                  <div class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ "Are you sure you want to delete the user '" + rightsSelected['user'] + "'@'" + rightsSelected['name'] + "'? This action cannot be undone." }}</div>                  
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn @click="removeRightSubmit" color="#00b16a">Delete</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn @click="sidebarDialog = false" color="#EF5354">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped src="@/styles/treeview.css"></style>

<style scoped>
.v-input__slot {
  background-color:#484848;
}
</style>

<script>
import { mapFields } from '../../../js/map-fields'
import EventBus from '../../../js/event-bus'

export default {
  data() {
    return {
      // Rights
      rightsSidebarSearch: '',
      rightsSidebarClicked: null,
      // Dialog
      sidebarDialog: false,
    }
  },
  props: { dialog: Boolean },
  mounted() {
    EventBus.$on('focus-search-bar', this.focusSearchBar);
  },
  computed: {
    ...mapFields([
      'rights',
      'rightsLoading',
      'rightsSelected',
      'rightsDiff',
      'rightsSidebarSelected',
      'rightsSidebarOpened',
    ], { path: 'client/connection' }),
  },
  watch: {
    dialog: function(val) {
      if (!val) {
        // Init Rights data
        this.rightsSidebarSelected = []
        this.rightsSidebarOpened = []
        this.rightsSidebarSearch = ''
        this.rightsSelected = {}
        this.rights = { sidebar: [], login: {}, server: {}, schema: [], resources: {}, syntax: '' }
        this.rightsDiff = { login: {}, server: { grant: [], revoke: [] }, schema: { grant: [], revoke: [] }, resources: {} }
        EventBus.$emit('reload-rights', 'edit')
      }
    }
  },
  methods: {
    focusSearchBar() {
      requestAnimationFrame(() => this.$refs.search.focus())
    },
    sidebarClick(event, item, active) {
      this.rightsSidebarClicked = item.id
      if (this.rightsLoading || 'children' in item) return
      if (active) event.stopPropagation()
      this.rightsSelected = {...item}
      new Promise((resolve) => { EventBus.$emit('get-rights', resolve, item['user'], item['name']) })
    },
    onRightClick(event) {
      event.preventDefault()
    },
    addRight() {
      this.rightsSidebarSelected = []
      this.rightsSelected = {}
      this.rights = { sidebar: this.rights['sidebar'], login: {}, server: {}, schema: [], resources: { max_queries: '0', max_updates: '0', max_connections: '0', max_simultaneous: '0' }, syntax: '' }
      this.rightsDiff = { login: {}, server: { grant: [], revoke: [] }, schema: { grant: [], revoke: [] }, resources: {}}
      EventBus.$emit('reload-rights', 'new')
    },
    removeRight() {
      this.sidebarDialog = true
    },
    removeRightSubmit() {
      this.sidebarDialog = false
      let query = "DROP USER '" + this.rightsSelected['user'] + "'@'" + this.rightsSelected['name'] + "';"
      new Promise((resolve) => { EventBus.$emit('apply-rights', resolve, [query]) })
      .then(() => { 
        this.rightsSidebarSelected = []
        this.rightsSelected = {}
      })  
    },
    cloneRight() {
      this.rightsSidebarSelected = []
      this.rightsSelected = {}
      this.rightsDiff = { login: {}, server: { grant: [], revoke: [] }, schema: { grant: [], revoke: [] }, resources: {}}
      EventBus.$emit('reload-rights', 'clone')
    },
    refreshRights() {
      new Promise((resolve) => { EventBus.$emit('get-rights', resolve) })
      .then(() => {
        if (Object.keys(this.rightsSelected).length != 0) new Promise((resolve) => { EventBus.$emit('get-rights', resolve, this.rightsSelected['user'], this.rightsSelected['name']) })
      })
    },
  }
}
</script>