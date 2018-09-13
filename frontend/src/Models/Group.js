import Base from './Base';


export default class Group extends Base {
    removeConfirmMessage() {
        return `Are you sure you want to remove group ${this.title}?`;
    }
    
    canSave() {
        return false;
    }
}

Group.model = {
	id: "group_id",
	root: "/membership/group",
	attributes: {
		created_at: null,
		updated_at: null,
		parent: "",
		name: "",
		title: "",
		description: "",
        num_members: 0,
	},
};