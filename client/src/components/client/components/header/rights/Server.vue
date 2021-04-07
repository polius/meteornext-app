<template>
  <div style="height:100%">
    <div style="height: calc(100% - 84px); position:relative; overflow-y:auto;">
      <v-row no-gutters style="padding:max(3%, 20px);">
        <v-col style="margin-right:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Database</div>
          <v-card style="height:337px">
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox :disabled="disabled" v-model="server" dense label="Create" value="create" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Drop" value="drop" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Alter" value="alter" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Index" value="index" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Trigger" value="trigger" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Event" value="event" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="References" value="references" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" value="create_temporary_tables" dense label="Create Temporary Tables" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" value="lock_tables" dense label="Lock Tables" hide-details style="margin:0px;"></v-checkbox>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col style="margin-left:10px; margin-right:10px;">
          <v-col style="padding:0px">
            <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Tables</div>
            <v-card>
              <v-card-text style="padding:10px; padding-bottom:15px">
                <v-checkbox :disabled="disabled" v-model="server" dense label="Select" value="select" hide-details style="margin:0px;"></v-checkbox>
                <v-checkbox :disabled="disabled" v-model="server" dense label="Insert" value="insert" hide-details style="margin:0px;"></v-checkbox>
                <v-checkbox :disabled="disabled" v-model="server" dense label="Update" value="update" hide-details style="margin:0px;"></v-checkbox>
                <v-checkbox :disabled="disabled" v-model="server" dense label="Delete" value="delete" hide-details style="margin:0px;"></v-checkbox>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col style="padding:0px">
            <div class="body-2" style="margin-left:10px; margin-bottom:5px; margin-top:10px">Views and Routines</div>
            <v-card>
              <v-card-text style="padding:10px; padding-bottom:15px">
                <v-checkbox :disabled="disabled" v-model="server" dense label="Show View" value="show_view" hide-details style="margin:0px;"></v-checkbox>
                <v-checkbox :disabled="disabled" v-model="server" dense label="Create View" value="create_view" hide-details style="margin:0px;"></v-checkbox>
                <v-checkbox :disabled="disabled" v-model="server" dense label="Create Routine" value="create_routine" hide-details style="margin:0px;"></v-checkbox>
                <v-checkbox :disabled="disabled" v-model="server" dense label="Alter Routine" value="alter_routine" hide-details style="margin:0px;"></v-checkbox>
                <v-checkbox :disabled="disabled" v-model="server" dense label="Execute" value="execute" hide-details style="margin:0px;"></v-checkbox>
              </v-card-text>
            </v-card>
          </v-col>
        </v-col>
        <v-col style="margin-left:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Administration and Replication</div>
          <v-card style="height:337px">
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox :disabled="disabled" v-model="server" dense label="Reload" value="reload" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Shutdown" value="shutdown" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="File" value="file" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Process" value="process" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Super" value="super" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Show Databases" value="show_databases" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Create User" value="create_user" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Replication Client" value="replication_client" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Replication Slave" value="replication_slave" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox :disabled="disabled" v-model="server" dense label="Grant" value="grant_option" hide-details style="margin:0px;"></v-checkbox>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>
    <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; position:relative; background-color:#484848; width:100%">
      <v-btn :disabled="disabled" @click="selectAll" text small title="Select All" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-check-square</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="disabled" @click="deselectAll" text small title="Deselect All" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">far fa-square</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
    </v-row>
  </div>
</template>

<script>
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      mode: '',
      disabled: true,
      server: {},
    }
  },
  computed: {
    ...mapFields([
      'rights',
      'rightsDiff',
      'rightsSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('reload-rights', this.reloadRights);
  },
  watch: {
    rightsSelected: function(val) {
      this.disabled = (Object.keys(val).length == 0 && this.mode == 'edit') ? true : false
    },
    server: {
      handler(obj) {
        this.computeDiff(obj)
      },
      deep: true
    },
  },  
  methods: {
    reloadRights(mode) {
      this.mode = mode
      const servers = JSON.parse(JSON.stringify(this.rights['server']))
      this.server = Object.keys(servers).filter(x => servers[x])
      if (mode == 'clone') this.rights['server'] = {}
    },
    computeDiff(obj) {
      this.rightsDiff['server'] = { 
        grant: obj.filter(x => !(x in this.rights['server']) || this.rights['server'][x] == false), 
        revoke: Object.keys(this.rights['server']).filter(x => this.rights['server'][x] == true && !obj.includes(x))
      }
    },
    selectAll() {
      this.server = ['create','drop','alter','index','trigger','event','references','create_temporary_tables','lock_tables','select','insert','update','delete','show_view','create_view','create_routine','alter_routine','execute','reload','shutdown','file','process','super','show_databases','create_user','replication_client','replication_slave','grant_option']
    },
    deselectAll() {
      this.server = []
    },
  }
}
</script>