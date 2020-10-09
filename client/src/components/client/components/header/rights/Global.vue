<template>
  <div style="height:100%">
    <div style="height: calc(100% - 84px);">
      <v-row no-gutters style="padding:max(2%, 20px);">
        <v-col style="margin-right:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Database and Tables</div>
          <v-card>
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox v-model="global.select" dense label="Select" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.insert" dense label="Insert" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.update" dense label="Update" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.delete" dense label="Delete" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.references" dense label="References" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.create" dense label="Create" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.drop" dense label="Drop" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.alter" dense label="Alter" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.index" dense label="Index" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.trigger" dense label="Trigger" hide-details style="margin:0px;"></v-checkbox>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col style="margin-left:10px; margin-right:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Views and Procedures</div>
          <v-card>
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox v-model="global.create_view" dense label="Create View" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.show_view" dense label="Show View" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.create_routine" dense label="Create Routine" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.alter_routine" dense label="Alter Routine" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.execute" dense label="Execute" hide-details style="margin:0px;"></v-checkbox>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col style="margin-left:10px;">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Administration and Replication</div>
          <v-card>
            <v-card-text style="padding:10px; padding-bottom:15px">
              <v-checkbox v-model="global.reload" dense label="Reload" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.shutdown" dense label="Shutdown" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.file" dense label="File" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.process" dense label="Process" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.super" dense label="Super" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.create_temp_table" dense label="Create Temp Table" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.lock_tables" dense label="Lock Tables" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.show_databases" dense label="Show Databases" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.create_user" dense label="Create User" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.grant" dense label="Grant" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.event" dense label="Event" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.replication_client" dense label="Replication Client" hide-details style="margin:0px;"></v-checkbox>
              <v-checkbox v-model="global.replication_slave" dense label="Replication Slave" hide-details style="margin:0px;"></v-checkbox>
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

export default {
  data() {
    return {
      global: {
        select: false, insert: false, update: false, delete: false, references: false, create: false, drop: false, alter: false, index: false, trigger: false,
        create_view: false, show_view: false, create_routine: false, alter_routine: false, execute: false,
        reload: false, shutdown: false, file: false, process: false, super: false, create_temp_table: false, lock_tables: false, show_databases: false, create_user: false, grant: false, event: false,replication_client: false, replication_slave: false
      }
    }
  },
  computed: {
  },
  methods: {
    selectAll() {
      for (let key of Object.keys(this.global)) this.global[key] = true
    },
    deselectAll() {
      for (let key of Object.keys(this.global)) this.global[key] = false
    },
  }
}
</script>