<template>
  <div style="height:100%">
    <div style="height: calc(100% - 84px);">
      <v-row no-gutters style="padding:max(2%, 20px);">
        <v-col style="margin-right:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Database and Tables</div>
          <v-card>
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox v-model="server['select']" dense label="Select" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['insert']" dense label="Insert" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['update']" dense label="Update" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['delete']" dense label="Delete" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['references']" dense label="References" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['create']" dense label="Create" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['drop']" dense label="Drop" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['alter']" dense label="Alter" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['index']" dense label="Index" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['trigger']" dense label="Trigger" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['event']" dense label="Event" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['create_tmp_table']" dense label="Create Temporary Table" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['lock_tables']" dense label="Lock Tables" hide-details style="margin:0px;"></v-checkbox>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col style="margin-left:10px; margin-right:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Views and Routines</div>
          <v-card>
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox v-model="server['show_view']" dense label="Show View" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['create_view']" dense label="Create View" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['create_routine']" dense label="Create Routine" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['alter_routine']" dense label="Alter Routine" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['execute']" dense label="Execute" hide-details style="margin:0px;"></v-checkbox>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col style="margin-left:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Administration and Replication</div>
          <v-card>
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox v-model="server['reload']" dense label="Reload" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['shutdown']" dense label="Shutdown" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['file']" dense label="File" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['process']" dense label="Process" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['super']" dense label="Super" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['show_db']" dense label="Show Databases" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['create_user']" dense label="Create User" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['grant']" dense label="Grant" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['repl_client']" dense label="Replication Client" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="server['repl_slave']" dense label="Replication Slave" hide-details style="margin:0px;"></v-checkbox>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>
    <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
      <v-btn @click="selectAll" text small title="Select All" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-check-square</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn @click="deselectAll" text small title="Deselect All" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">far fa-square</v-icon></v-btn>
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
      server: {},
    }
  },
  computed: {
    ...mapFields([
      'rights',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('RELOAD_RIGHTS', this.reloadRights);
  },
  watch: {
    server: {
      handler() {
        let change = JSON.stringify(this.rights['server']) !== JSON.stringify(this.server)
        console.log("change: " + change.toString())
      },
      deep: true
    },
  },  
  methods: {
    reloadRights() {
      this.server = JSON.parse(JSON.stringify(this.rights['server']))
    },
    selectAll() {
      for (let key of Object.keys(this.server)) this.server[key] = true
    },
    deselectAll() {
      for (let key of Object.keys(this.server)) this.server[key] = false
    },
  }
}
</script>