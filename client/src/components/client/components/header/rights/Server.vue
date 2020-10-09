<template>
  <div style="height:100%">
    <div style="height: calc(100% - 84px);">
      <v-row no-gutters style="padding:max(2%, 20px);">
        <v-col style="margin-right:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Database and Tables</div>
          <v-card>
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox v-model="rights['server'].select" dense label="Select" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].insert" dense label="Insert" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].update" dense label="Update" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].delete" dense label="Delete" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].references" dense label="References" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].create" dense label="Create" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].drop" dense label="Drop" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].alter" dense label="Alter" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].index" dense label="Index" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].trigger" dense label="Trigger" hide-details style="margin:0px;"></v-checkbox>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col style="margin-left:10px; margin-right:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Views and Procedures</div>
          <v-card>
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox v-model="rights['server'].create_view" dense label="Create View" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].show_view" dense label="Show View" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].create_routine" dense label="Create Routine" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].alter_routine" dense label="Alter Routine" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].execute" dense label="Execute" hide-details style="margin:0px;"></v-checkbox>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col style="margin-left:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Administration and Replication</div>
          <v-card>
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox v-model="rights['server'].reload" dense label="Reload" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].shutdown" dense label="Shutdown" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].file" dense label="File" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].process" dense label="Process" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].super" dense label="Super" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].create_temp_table" dense label="Create Temp Table" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].lock_tables" dense label="Lock Tables" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].show_databases" dense label="Show Databases" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].create_user" dense label="Create User" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].grant" dense label="Grant" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].event" dense label="Event" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].replication_client" dense label="Replication Client" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="rights['server'].replication_slave" dense label="Replication Slave" hide-details style="margin:0px;"></v-checkbox>
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
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
    }
  },
  props: { tab: Number },
  computed: {
    ...mapFields([
      'rights',
    ], { path: 'client/connection' }),
  },
  methods: {
    selectAll() {
      for (let key of Object.keys(this.rights['server'])) this.rights['server'][key] = true
    },
    deselectAll() {
      for (let key of Object.keys(this.rights['server'])) this.rights['server'][key] = false
    },
  }
}
</script>